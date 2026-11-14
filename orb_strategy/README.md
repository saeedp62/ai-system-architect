# 15-minute Opening Range Breakout (first three 5-minute candles)

A rule-based day-trading strategy for liquid US index products (ES/MES, NQ/MNQ, RTY/M2K futures or
SPY/QQQ/IWM), with a backtest on 15 years of 1-minute data. Standalone: needs only `pandas` and `numpy`.

**Read this first.** No strategy is "proven". What is here is a strategy whose rules were fixed on
2005-2014 data and then kept their edge on 2015-2020 data they had never seen. The edge is small,
depends heavily on low trading costs, and comes from a few big days. Details under *Results* and *Limits*.

## Rules

All times New York. Use 5-minute candles for the range and a resting stop order for entry.

1. **Range (09:30-09:45).** After the third 5-minute candle closes, mark the high and low of the
   three candles. Midpoint = (high + low) / 2.
2. **Expected direction.** Take the price at 09:45 and compare it with (a) the 09:30 open and
   (b) yesterday's 16:00 close.
   - above both -> **long only** today
   - below both -> **short only** today
   - mixed -> **no trade** today
3. **Entry.** Long: buy-stop at the range high. Short: sell-stop at the range low. Only the first
   break of the range counts. If price breaks the *wrong* side first, the day is over - cancel the order.
   No entries after 12:00.
4. **Stop loss.** At the range midpoint. This distance is 1R.
5. **Exit.** No profit target. Hold until stopped or until 15:55, then close at market. Never hold overnight.
6. **Size.** Risk a fixed 0.25-0.5% of the account per trade:
   `position = (equity x risk%) / (entry - stop)`, capped at 4x notional leverage.
   One trade per instrument per day, no re-entry.

Expect to be stopped out about three days in four. The profit comes from the remaining days,
where the average winner is about 3.3R. Adding a profit target made results worse in testing.

## Why these rules

- **Direction filter.** The first part of the session tends to predict the rest of the day
  (intraday momentum; Gao, Han, Li & Zhou, *Journal of Financial Economics* 2018). In the backtest,
  breakouts with the opening move earned money and breakouts against it lost money, in both periods.
- **Tight stop, no target.** This is the structure of the published opening-range studies by
  Zarattini & Aziz (2023) and Zarattini, Barbon & Aziz (2024): small fixed loss, winners run to the close.
- **Textbook version does not work.** Trading either side with the stop at the far edge of the range
  was flat to negative after costs in both periods.

## Results

1-minute Oanda CFD bars for S&P 500, Nasdaq 100 and Russell 2000, January 2005 - May 2020.
Net of 1 basis point round-trip cost, 0.5% risk per trade. Rules were chosen on 2005-2014 only.

| | Trades | Win % | Avg R / trade | Profit factor | CAGR | Max drawdown |
|---|---|---|---|---|---|---|
| **In-sample 2005-2014** | | | | | | |
| S&P 500 | 1,072 | 23.1 | +0.108 | 1.13 | 5.0% | -23.3% |
| Nasdaq 100 | 1,116 | 25.8 | +0.146 | 1.19 | 8.0% | -20.5% |
| Russell 2000 | 1,232 | 25.9 | +0.125 | 1.16 | 7.0% | -26.0% |
| All three, risk split in thirds | 3,420 | 25.0 | +0.127 | 1.16 | 7.3% | -17.7% |
| **Out-of-sample 2015 - May 2020** | | | | | | |
| S&P 500 | 606 | 25.2 | +0.077 | 1.09 | 3.5% | -14.3% |
| Nasdaq 100 | 634 | 28.9 | +0.198 | 1.27 | 10.3% | -11.8% |
| Russell 2000 | 690 | 27.0 | +0.096 | 1.13 | 5.8% | -14.9% |
| All three, risk split in thirds | 1,930 | 27.0 | +0.124 | 1.16 | 7.0% | -8.5% |

Out-of-sample comparisons (all three pooled):

| Variant | Avg R / trade | Profit factor |
|---|---|---|
| Final rules, 0 bp cost | +0.189 | 1.26 |
| Final rules, 1 bp cost | +0.124 | 1.16 |
| Final rules, 2 bp cost | +0.058 | 1.07 |
| Final rules, 3 bp cost | -0.008 | 0.99 |
| Textbook ORB (either side, stop at far edge) | +0.002 | 1.00 |
| Trading against the expected direction | -0.188 | 0.78 |

Out-of-sample every calendar year was positive (2015-2020). In-sample, 2005 and 2010 were losing years.

## Limits

- **Statistical strength is moderate.** The t-statistic of daily P&L is 2.1 in-sample and 1.7
  out-of-sample. That is evidence of an edge, not certainty. Out-of-sample is five years.
- **Costs decide everything.** The edge is gone at 3 bp round trip. One basis point is realistic for
  ES/NQ futures or SPY/QQQ today; it is not realistic for CFDs with wide spreads or for small-cap stocks.
- **Profit is concentrated.** The best 1% of trades produce roughly all of the net profit. Missing a
  few trend days, or cutting winners early, removes the edge.
- **Losing streaks are long.** The longest run of losing trades was 41 in-sample and 24 out-of-sample
  (counting all three indices). Size so that this is survivable.
- **Data.** CFD mid prices, not exchange futures or ETF prints; no real volume. Data ends May 2020,
  so 2020-2026 is untested here. Stop orders are assumed filled at the stop price (at the open on gaps).
- **The three indices are one bet.** They trigger together on most days. Trading all three is not
  diversification; split the risk budget between them.
- **Observed, not used as a rule:** days when all three indices triggered earned about +0.23R to +0.32R
  per trade; days when only one triggered were negative. Worth testing as a confirmation filter on new data.

Paper-trade it for at least 2-3 months and compare your fills with the backtest before using real money.
This is research, not financial advice.

## Reproduce

```bash
python prepare_data.py data     # downloads ~700 MB of public minute data, writes data/*.pkl
python run_backtest.py data     # prints the tables above plus yearly breakdowns
```

- `orb.py` - strategy rules (`Params`) and the event-driven backtester (`run`, `stats`).
- `run_backtest.py` - the frozen parameters (`FINAL`) and the in-sample / out-of-sample report.
- `prepare_data.py` - data download and session filtering.

Backtest conventions: stop wins when stop and exit fall in the same minute; a breakout bar that
also touches the stop and closes back inside is booked as a full loss; a minute that breaks both
sides of the range is skipped; ATR and yesterday's close use only prior days.

## References

- Zarattini & Aziz, *Can Day Trading Really Be Profitable?* (2023), SSRN 4416622
- Zarattini, Barbon & Aziz, *A Profitable Day Trading Strategy for the U.S. Equity Market* (2024), SSRN 4729284
- Gao, Han, Li & Zhou, *Market Intraday Momentum*, Journal of Financial Economics 129 (2018)
