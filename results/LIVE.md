# Daily record (generated)

Forecast days scored: 106. Resolved rows: 20280. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    103 |         0.1035 | 0.3218 |  0.485  |  0.8831 |                 0.2462 |      0.1799 |      0.3481 |
| gbm                  |    106 |         0.1074 | 0.3325 |  0.4473 |  0.8447 |                 0.2246 |      0.1817 |      0.3429 |
| sarima               |    106 |         0.1145 | 0.3542 |  0.5641 |  0.9135 |                 0.1701 |      0.2204 |      0.2029 |
| har_seasonal         |    106 |         0.1236 | 0.39   |  0.4465 |  0.8671 |                 0.1066 |      0.2376 |      0.1404 |
| prophet              |    106 |         0.1236 | 0.3772 |  0.5012 |  0.8479 |                 0.0966 |      0.2583 |      0.0655 |
| har                  |    106 |         0.1267 | 0.4005 |  0.4737 |  0.8722 |                 0.0958 |      0.2414 |      0.1269 |
| persistence          |    106 |         0.1414 | 0.4416 |  0.5256 |  0.9053 |                 0      |      0.2765 |      0      |
| seasonal_persistence |    106 |         0.1572 | 0.485  |  0.4654 |  0.866  |                -0.1499 |      0.3256 |     -0.1779 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 26 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1112.

Matched on the 103 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.35 on the day-level error (0.20 to 0.50). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

