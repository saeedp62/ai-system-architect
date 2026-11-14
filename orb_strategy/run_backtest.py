"""Backtest the frozen 15-minute ORB rules: in-sample 2005-2014, out-of-sample 2015 - May 2020.

Usage:  python run_backtest.py [data_dir]      (run prepare_data.py first)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from orb import Params, build_days, replace, run, split, stats

SYMBOLS = ["SPX500_USD", "NAS100_USD", "US2000_USD"]
CUT = "2015-01-01"  # everything from here on was not looked at while choosing the rules

V1 = Params(direction="bias", bias_ref="agree", entry="stop", stop="mid", target_r=None,
            last_entry="12:00", exit_time="15:55", cost_bps=1.0, risk_pct=0.5)
# v2 "gap and go": v1 plus an overnight gap >= 0.3 ATR that the first 15 minutes extended
FINAL = replace(V1, bias_ref="open", min_gap_atr=0.3)
NAIVE = replace(V1, direction="both", stop="range")  # textbook ORB: either side, stop at far edge


def day_t(t: pd.DataFrame) -> float:
    """t-statistic of daily P&L in R. Same-day trades on the three (highly correlated) indices are
    summed into one observation, so the pooled row does not triple-count the same market move."""
    d = t.groupby("date").r.sum()
    return float(d.mean() / d.std(ddof=1) * np.sqrt(len(d)))


def line(label: str, t: pd.DataFrame) -> str:
    s = stats(t.sort_values("date"))
    return (f"{label:<26}{s['trades']:>6}{s['win']:>7.1f}{s['avg_r']:>8.3f}{s['pf']:>6.2f}"
            f"{day_t(t):>7.2f}{s['cagr']:>7.1f}{s['sharpe']:>7.2f}{s['max_dd']:>8.1f}")


HEAD = f"{'':<26}{'trades':>6}{'win%':>7}{'avgR':>8}{'PF':>6}{'t':>7}{'CAGR%':>7}{'Sharpe':>7}{'maxDD%':>8}"

if __name__ == "__main__":
    data_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    days = {s: build_days(pd.read_pickle(data_dir / f"{s}.pkl")) for s in SYMBOLS}
    for name, k in (("IN-SAMPLE 2005-2014", 0), ("OUT-OF-SAMPLE 2015-2020", 1)):
        part = {s: split(days[s], CUT)[k] for s in SYMBOLS}
        res = {s: run(part[s], FINAL) for s in SYMBOLS}
        allt = pd.concat(res.values())
        print(f"\n=== {name} ===  (net of {FINAL.cost_bps} bp round trip, {FINAL.risk_pct}% risk/trade)")
        print(HEAD)
        for s in SYMBOLS:
            print(line(s, res[s]))
        n_days_traded = allt.date.nunique()
        allt = allt.assign(ret=allt.ret / len(SYMBOLS))  # pooled rows split the risk budget three ways
        print(line("all three, risk split /3", allt))
        print(line("  longs only", allt[allt.side > 0]))
        print(line("  shorts only", allt[allt.side < 0]))
        print("-- comparisons, all three pooled")
        for label, p in (("textbook ORB, both sides", NAIVE),
                         ("v1 (no gap filter)", V1),
                         ("gap >= 0.2 ATR", replace(FINAL, min_gap_atr=0.2)),
                         ("gap >= 0.4 ATR", replace(FINAL, min_gap_atr=0.4)),
                         ("stop at far edge", replace(FINAL, stop="range")),
                         ("final rules, 0 bp cost", replace(FINAL, cost_bps=0)),
                         ("final rules, 2 bp cost", replace(FINAL, cost_bps=2)),
                         ("final rules, 3 bp cost", replace(FINAL, cost_bps=3)),
                         ("final rules, 5 bp cost", replace(FINAL, cost_bps=5)),
                         ("small-gap days (<0.3 ATR)", None)):
            if p is None:
                tt = pd.concat([run(part[s], replace(FINAL, min_gap_atr=0)) for s in SYMBOLS])
                tt = tt[tt.side * tt.gap_atr < 0.3]
                print(line(label, tt.assign(ret=tt.ret / len(SYMBOLS))))
                continue
            tt = pd.concat([run(part[s], p) for s in SYMBOLS])
            print(line(label, tt.assign(ret=tt.ret / len(SYMBOLS))))
        yr = allt.groupby(pd.to_datetime(allt.date).dt.year).r.agg(["count", "mean", "sum"]).round(3)
        print("-- by year (R):")
        print(yr.rename(columns={"count": "trades", "mean": "avgR", "sum": "totalR"}).to_string())
        n_same = allt.groupby("date").r.transform("size")
        print("-- by how many of the three indices triggered that day (diagnostic, not a rule):")
        print(allt.groupby(n_same).r.agg(["count", "mean"]).round(3)
              .rename(columns={"count": "trades", "mean": "avgR"}).to_string())
        top = allt.r.nlargest(max(1, len(allt) // 100)).sum()
        print(f"best 1% of trades contribute {top:.0f}R of {allt.r.sum():.0f}R total")
        print("days with at least one trade:", n_days_traded)
        print("exit reasons:", allt.reason.value_counts().to_dict(),
              "| avg winner R:", round(allt.r[allt.r > 0].mean(), 2),
              "| longest losing streak:", int((allt.sort_values("date").r <= 0).astype(int)
                                              .groupby((allt.sort_values("date").r > 0).cumsum()).sum().max()))
