# Daily record (generated)

Forecast days scored: 114. Resolved rows: 21816. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    111 |         0.1046 | 0.325  |  0.4775 |  0.8735 |                 0.2426 |      0.184  |      0.3485 |
| gbm                  |    114 |         0.1081 | 0.3345 |  0.4401 |  0.841  |                 0.2242 |      0.1855 |      0.3438 |
| sarima               |    114 |         0.116  | 0.36   |  0.5534 |  0.9083 |                 0.1627 |      0.2273 |      0.1958 |
| har_seasonal         |    114 |         0.1233 | 0.3896 |  0.4477 |  0.8699 |                 0.1142 |      0.2375 |      0.1599 |
| har                  |    114 |         0.1263 | 0.3998 |  0.4784 |  0.8743 |                 0.1038 |      0.2413 |      0.1465 |
| prophet              |    114 |         0.127  | 0.3865 |  0.4938 |  0.8439 |                 0.0767 |      0.2712 |      0.0406 |
| persistence          |    114 |         0.1421 | 0.4455 |  0.5205 |  0.9042 |                 0      |      0.2827 |      0      |
| seasonal_persistence |    114 |         0.1553 | 0.4796 |  0.4686 |  0.8706 |                -0.1298 |      0.3181 |     -0.1254 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 34 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1127.

Matched on the 111 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.33) and 0.35 on the day-level error (0.21 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

