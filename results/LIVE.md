# Daily record (generated)

Forecast days scored: 88. Resolved rows: 16824. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     85 |         0.1    | 0.3128 |  0.4951 |  0.8946 |                 0.2577 |      0.1593 |      0.4035 |
| gbm                  |     88 |         0.1066 | 0.3301 |  0.4498 |  0.8461 |                 0.2162 |      0.17   |      0.3654 |
| sarima               |     88 |         0.1111 | 0.3426 |  0.5777 |  0.9205 |                 0.1797 |      0.2042 |      0.2379 |
| prophet              |     88 |         0.1209 | 0.3711 |  0.4995 |  0.8499 |                 0.1005 |      0.249  |      0.0707 |
| har_seasonal         |     88 |         0.1216 | 0.3845 |  0.446  |  0.8736 |                 0.1039 |      0.2231 |      0.1673 |
| har                  |     88 |         0.1247 | 0.3948 |  0.473  |  0.8788 |                 0.0914 |      0.226  |      0.1564 |
| persistence          |     88 |         0.1384 | 0.4353 |  0.5223 |  0.9134 |                 0      |      0.2679 |      0      |
| seasonal_persistence |     88 |         0.1546 | 0.478  |  0.4721 |  0.8717 |                -0.1492 |      0.3112 |     -0.1615 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 8 forecast days scored since the change, prophet leads with a mean pinball loss of 0.1009.

Matched on the 85 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.36) and 0.40 on the day-level error (0.24 to 0.57). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

