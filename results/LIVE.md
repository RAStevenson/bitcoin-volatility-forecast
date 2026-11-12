# Daily record (generated)

Forecast days scored: 100. Resolved rows: 19128. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     97 |         0.1009 | 0.3148 |  0.4897 |  0.8887 |                 0.2554 |      0.1711 |      0.3651 |
| gbm                  |    100 |         0.1063 | 0.3295 |  0.4492 |  0.8479 |                 0.2233 |      0.1751 |      0.3519 |
| sarima               |    100 |         0.1125 | 0.3478 |  0.5692 |  0.9192 |                 0.1749 |      0.2134 |      0.21   |
| prophet              |    100 |         0.1183 | 0.3636 |  0.5088 |  0.8571 |                 0.125  |      0.242  |      0.1042 |
| har_seasonal         |    100 |         0.1227 | 0.388  |  0.4433 |  0.8696 |                 0.1018 |      0.2335 |      0.1356 |
| har                  |    100 |         0.1261 | 0.3988 |  0.47   |  0.8746 |                 0.0882 |      0.2372 |      0.1221 |
| persistence          |    100 |         0.1396 | 0.437  |  0.5258 |  0.9108 |                 0      |      0.2701 |      0      |
| seasonal_persistence |    100 |         0.159  | 0.4902 |  0.4617 |  0.8633 |                -0.1753 |      0.3278 |     -0.2135 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 20 forecast days scored since the change, prophet leads with a mean pinball loss of 0.1001.

Matched on the 97 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.37 on the day-level error (0.21 to 0.52). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

