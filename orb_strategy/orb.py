"""15-minute Opening Range Breakout (first three 5-minute candles) - rules and backtester.

All times are America/New_York. Input is 1-minute regular-hours bars so that entries,
stops and targets are resolved in the order they actually happened.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

OPEN_MIN = 9 * 60 + 30  # 09:30


@dataclass(frozen=True)
class Params:
    or_minutes: int = 15           # three 5-minute candles
    direction: str = "bias"        # "bias" = only in the expected direction, "both", "fade"
    bias_ref: str = "open"         # expected direction = sign of (09:45 price - ref): "open", "prev_close", "agree"
    entry: str = "stop"            # "stop" = resting stop order at the range edge, "close5" = 5-min close outside
    stop: str = "range"            # "range" = opposite edge, "mid" = range midpoint, "atr" = atr_stop * ATR14
    atr_stop: float = 0.10
    target_r: float | None = None  # profit target in R; None = hold to the time exit
    last_entry: str = "12:00"      # no new entries at/after this time
    exit_time: str = "15:55"       # flat by this time, always
    min_or_atr: float = 0.0        # skip days whose range is narrower than this fraction of ATR14
    max_or_atr: float = 9.9        # skip days whose range is wider than this fraction of ATR14
    cost_bps: float = 2.0          # round-trip cost (spread + slippage + fees) in basis points of price
    risk_pct: float = 0.5          # % of equity risked per trade
    max_leverage: float = 4.0


def _hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def build_days(df: pd.DataFrame, min_bars: int = 200) -> list[dict]:
    """Split 1-minute RTH bars into per-day numpy arrays and attach yesterday's ATR14."""
    days = []
    minute = (df.index.hour * 60 + df.index.minute).to_numpy()
    date = df.index.date
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    bounds = np.flatnonzero(np.r_[True, date[1:] != date[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a < min_bars:
            continue  # holiday / broken session
        days.append(dict(date=date[a], m=minute[a:b], o=o[a:b], h=h[a:b], l=l[a:b], c=c[a:b]))
    hi = np.array([d["h"].max() for d in days])
    lo = np.array([d["l"].min() for d in days])
    cl = np.array([d["c"][-1] for d in days])
    pc = np.r_[np.nan, cl[:-1]]
    tr = np.nanmax(np.c_[hi - lo, np.abs(hi - pc), np.abs(lo - pc)], axis=1)
    atr = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()  # known before today's open
    for d, a, y in zip(days, atr, pc):
        d["atr"], d["pc"] = a, y
    return days


def run(days: list[dict], p: Params) -> pd.DataFrame:
    """Return one row per trade. At most one trade per day, never held overnight."""
    last_entry, exit_t = _hm(p.last_entry), _hm(p.exit_time)
    or_end = OPEN_MIN + p.or_minutes
    rows = []
    for d in days:
        m, o, h, l, c, atr = d["m"], d["o"], d["h"], d["l"], d["c"], d["atr"]
        if not np.isfinite(atr):
            continue
        in_or = m < or_end
        if in_or.sum() < p.or_minutes * 0.6 or m[0] > OPEN_MIN + 2:
            continue
        orh, orl = h[in_or].max(), l[in_or].min()
        width = orh - orl
        if width <= 0 or not (p.min_or_atr <= width / atr <= p.max_or_atr):
            continue
        or_close = c[in_or][-1]
        b_open, b_prev = np.sign(or_close - o[0]), np.sign(or_close - d["pc"])
        if p.bias_ref == "open":      # net direction of the three candles
            bias = b_open
        elif p.bias_ref == "prev_close":  # direction since yesterday's close (gap + first 15 min)
            bias = b_prev
        else:                         # both must agree, otherwise no trade
            bias = b_open if b_open == b_prev else 0
        if p.direction == "both":
            allow_long = allow_short = True
        elif p.direction == "bias":
            allow_long, allow_short = bias > 0, bias < 0
        else:  # fade: trade only against the opening move
            allow_long, allow_short = bias < 0, bias > 0

        # ---- entry -------------------------------------------------------
        side, entry, i_entry = 0, np.nan, -1
        idx = np.flatnonzero((m >= or_end) & (m < last_entry))
        if p.entry == "stop":
            for i in idx:
                up, dn = h[i] > orh, l[i] < orl
                if up and dn:  # both edges inside one minute: order unknown, stand aside
                    break
                if up:
                    if allow_long:
                        side, entry, i_entry = 1, max(orh, o[i]), i
                    break  # first breakout decides the day
                if dn:
                    if allow_short:
                        side, entry, i_entry = -1, min(orl, o[i]), i
                    break
        else:  # close5: a completed 5-minute candle closes outside the range, enter next bar open
            for i in idx:
                if m[i] % 5 != 4 or i + 1 >= len(m) or m[i + 1] >= last_entry:
                    continue
                if c[i] > orh:
                    if allow_long:
                        side, entry, i_entry = 1, o[i + 1], i + 1
                    break
                if c[i] < orl:
                    if allow_short:
                        side, entry, i_entry = -1, o[i + 1], i + 1
                    break
        if side == 0:
            continue

        # ---- stop / target ----------------------------------------------
        if p.stop == "range":
            stop = orl if side > 0 else orh
        elif p.stop == "mid":
            stop = (orh + orl) / 2
        else:
            stop = entry - side * p.atr_stop * atr
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        target = entry + side * p.target_r * risk if p.target_r else None

        # ---- manage -------------------------------------------------------
        exit_px, reason = np.nan, "time"
        # On the entry bar of a stop entry only the part after the fill counts, which 1-minute
        # bars cannot show. Be conservative: if that bar also touched the stop and closed back
        # below the entry (above, for shorts), book a full stop-out.
        start = i_entry
        if p.entry == "stop":
            start = i_entry + 1
            k = i_entry
            touched = l[k] <= stop if side > 0 else h[k] >= stop
            if touched and side * (c[k] - entry) < 0:
                exit_px, reason, start = stop, "stop", len(m)
        for j in range(start, len(m)):
            if m[j] >= exit_t:
                exit_px = o[j]
                break
            hit_stop = l[j] <= stop if side > 0 else h[j] >= stop
            hit_tgt = target is not None and (h[j] >= target if side > 0 else l[j] <= target)
            if hit_stop:  # stop wins any tie inside a bar (conservative)
                gap = o[j] < stop if side > 0 else o[j] > stop
                exit_px, reason = (o[j] if gap else stop), "stop"
                break
            if hit_tgt:
                exit_px, reason = target, "target"
                break
        if np.isnan(exit_px):
            exit_px = c[-1]

        gross = side * (exit_px - entry)
        cost = entry * p.cost_bps / 1e4
        r = (gross - cost) / risk
        size = min(p.risk_pct / 100 / (risk / entry), p.max_leverage)  # notional / equity
        rows.append(dict(date=d["date"], side=side, entry=entry, stop=stop, exit=exit_px,
                         reason=reason, or_atr=width / atr, r=r, gross_r=gross / risk,
                         ret=size * (gross - cost) / entry))
    return pd.DataFrame(rows)


def stats(t: pd.DataFrame, n_days: int | None = None) -> dict:
    if t.empty:
        return dict(trades=0)
    eq = (1 + t["ret"]).cumprod()
    years = (pd.Timestamp(t["date"].iloc[-1]) - pd.Timestamp(t["date"].iloc[0])).days / 365.25
    wins, losses = t.r[t.r > 0].sum(), -t.r[t.r <= 0].sum()
    n_days = n_days or int(years * 252)
    daily = t["ret"].sum() / n_days, np.sqrt((t["ret"] ** 2).sum() / n_days)
    return dict(
        trades=len(t), win=round(100 * (t.r > 0).mean(), 1), avg_r=round(t.r.mean(), 3),
        gross_r=round(t.gross_r.mean(), 3), pf=round(wins / losses, 2) if losses else np.inf,
        t_stat=round(t.r.mean() / t.r.std(ddof=1) * np.sqrt(len(t)), 2),
        cagr=round(100 * (eq.iloc[-1] ** (1 / max(years, 0.1)) - 1), 1),
        sharpe=round(daily[0] / daily[1] * np.sqrt(252), 2) if daily[1] else 0.0,
        max_dd=round(100 * (eq / eq.cummax() - 1).min(), 1),
    )


def split(days: list[dict], cut: str) -> tuple[list[dict], list[dict]]:
    cut_d = pd.Timestamp(cut).date()
    return [d for d in days if d["date"] < cut_d], [d for d in days if d["date"] >= cut_d]


__all__ = ["Params", "build_days", "run", "stats", "split", "replace"]
