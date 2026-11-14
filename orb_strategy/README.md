# 15-minute Opening Range Breakout (first three 5-minute candles)

A rule-based day-trading strategy for liquid US index products (ES/MES, NQ/MNQ, RTY/M2K futures or
SPY/QQQ/IWM), with a backtest on 15 years of 1-minute data. Standalone: needs only `pandas` and `numpy`.

**Read this first.** No strategy is "proven". Version 2 below was designed on 2005-2014 data only
and then run once on 2015-2020 data. It kept a clear edge there, at about two thirds of its
in-sample size. Details under *Results* and *Limits*.

## What was wrong with version 1

Version 1 traded every day the first 15 minutes pointed one way. Its edge (+0.12R per trade) was too
thin: it died at 3 bp of cost and relied on a handful of huge days.

Splitting the 2005-2014 trades by what was known at 09:45 showed where the money actually came from:

| Overnight gap, measured in the trade direction | Trades | Avg R |
|---|---|---|
| Gap of 0.3 ATR or more **with** the first-15-minute move | 813 | +0.48 |
| Gap of 0.3 ATR or more **against** it | 1,189 | +0.20 |
| Small gap (under 0.3 ATR either way) | 3,409 | -0.04 |

An opening-range breakout on a day with no overnight news is noise. It works when the market gaps on
a catalyst and the first 15 minutes confirm the gap instead of fading it ("gap and go"). This is the
index version of the "stocks in play" filter in the Zarattini, Barbon & Aziz study.

## Rules (version 2, "gap and go")

All times New York. ATR = 14-day average true range of the regular session, as of yesterday.

1. **Range (09:30-09:45).** Mark the high, low and midpoint of the first three 5-minute candles.
2. **Setup - both must be true at 09:45, otherwise no trade today:**
   - **Gap:** today's 09:30 open is at least 0.3 ATR away from yesterday's 16:00 close.
   - **Confirmation:** the 09:45 price is beyond the 09:30 open in the same direction as the gap
     (gap up and still rising -> long only; gap down and still falling -> short only).
3. **Entry.** Buy-stop at the range high (long) or sell-stop at the range low (short). Only the first
   break of the range counts; if the wrong side breaks first, cancel. No entries after 12:00.
4. **Stop loss.** Range midpoint. This distance is 1R.
5. **Exit.** No profit target. Hold until stopped or 15:55, then close. Never hold overnight.
6. **Size.** Risk a fixed 0.25-0.5% of the account per trade:
   `position = (equity x risk%) / (entry - stop)`, capped at 4x notional leverage.
   One trade per instrument per day, no re-entry.

Expect a setup on roughly one day in four, a win rate near 31%, and winners averaging about 3.4R.

## Results

1-minute Oanda CFD bars for S&P 500, Nasdaq 100 and Russell 2000, January 2005 - May 2020.
Net of 1 basis point round-trip cost, 0.5% risk per trade.

| | Trades | Win % | Avg R / trade | Profit factor | CAGR | Max drawdown |
|---|---|---|---|---|---|---|
| **In-sample 2005-2014** | | | | | | |
| S&P 500 | 304 | 30.3 | +0.416 | 1.55 | 6.2% | -5.8% |
| Nasdaq 100 | 272 | 33.8 | +0.487 | 1.72 | 6.6% | -5.3% |
| Russell 2000 | 237 | 33.8 | +0.548 | 1.82 | 6.6% | -7.9% |
| All three, risk split in thirds | 813 | 32.5 | +0.478 | 1.68 | 6.6% | -4.2% |
| **Out-of-sample 2015 - May 2020** | | | | | | |
| S&P 500 | 248 | 29.4 | +0.213 | 1.28 | 3.3% | -8.4% |
| Nasdaq 100 | 211 | 35.5 | +0.482 | 1.72 | 9.1% | -8.9% |
| Russell 2000 | 168 | 27.4 | +0.270 | 1.37 | 4.1% | -7.2% |
| All three, risk split in thirds | 627 | 30.9 | +0.319 | 1.44 | 5.6% | -6.1% |

CAGR scales with the risk setting; "split in thirds" means about 0.17% risk per trade.

Out-of-sample comparisons (all three pooled):

| Variant | Trades | Avg R / trade | Profit factor |
|---|---|---|---|
| **Version 2 (final)** | 627 | +0.319 | 1.44 |
| Version 1 (no gap filter) | 1,930 | +0.124 | 1.16 |
| Textbook ORB (either side, stop at far edge) | 4,036 | +0.002 | 1.00 |
| Same rules on small-gap days only | 2,698 | -0.133 | 0.84 |
| Gap threshold 0.2 ATR | 851 | +0.256 | 1.34 |
| Gap threshold 0.4 ATR | 445 | +0.261 | 1.35 |
| Version 2 at 2 bp cost | 627 | +0.252 | 1.33 |
| Version 2 at 3 bp cost | 627 | +0.185 | 1.23 |
| Version 2 at 5 bp cost | 627 | +0.051 | 1.06 |

All six out-of-sample years were positive. In-sample, 2005 and 2012 were slightly negative.

## Limits

- **The edge shrank out-of-sample** (+0.48R to +0.32R). Expect live results below the backtest again.
- **Statistical strength is decent, not overwhelming.** The t-statistic of daily P&L is 3.9 in-sample
  and 2.5 out-of-sample, on 358 out-of-sample trading days.
- **The out-of-sample period is not perfectly clean.** It had already been used once to check
  version 1. The gap rule itself was chosen from 2005-2014 data only.
- **Shorts are weaker than longs** (+0.21R vs +0.39R out-of-sample), and the S&P 500 is the weakest
  of the three. Nasdaq 100 carried the most edge in both periods.
- **Still a low win rate.** The longest losing streak was 25 trades in-sample and 18 out-of-sample.
  The best 1% of trades made 38% of the out-of-sample profit.
- **Data.** CFD mid prices, not exchange futures or ETF prints. Data ends May 2020, so 2020-2026 is
  untested. Stop orders are assumed filled at the stop price (at the open on gaps).
- **The three indices are one bet.** They usually trigger together; split the risk budget between them.
- **Not tested on single stocks.** A proper Tesla test needs several years of intraday bars, which
  were not available here.

Paper-trade it for at least 2-3 months and compare your fills with the backtest before using real money.
This is research, not financial advice.

## Reproduce

```bash
python prepare_data.py data     # downloads ~700 MB of public minute data, writes data/*.pkl
python run_backtest.py data     # prints the tables above plus yearly breakdowns
```

- `orb.py` - strategy rules (`Params`) and the event-driven backtester (`run`, `stats`).
- `run_backtest.py` - the frozen parameters (`FINAL` = version 2, `V1` = version 1) and the in-sample / out-of-sample report.
- `prepare_data.py` - data download and session filtering.

Backtest conventions: stop wins when stop and exit fall in the same minute; a breakout bar that
also touches the stop and closes back inside is booked as a full loss; a minute that breaks both
sides of the range is skipped; ATR and yesterday's close use only prior days.

## References

- Zarattini & Aziz, *Can Day Trading Really Be Profitable?* (2023), SSRN 4416622
- Zarattini, Barbon & Aziz, *A Profitable Day Trading Strategy for the U.S. Equity Market* (2024), SSRN 4729284
- Gao, Han, Li & Zhou, *Market Intraday Momentum*, Journal of Financial Economics 129 (2018)
