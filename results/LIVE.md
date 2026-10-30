# Daily record (generated)

Forecast days scored: 87. Resolved rows: 16632. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     84 |         0.1002 | 0.3133 |  0.495  |  0.8943 |                 0.2559 |      0.161  |      0.397  |
| gbm                  |     87 |         0.1062 | 0.3294 |  0.4516 |  0.8482 |                 0.2189 |      0.168  |      0.3728 |
| sarima               |     87 |         0.1109 | 0.3418 |  0.5776 |  0.9195 |                 0.1797 |      0.2023 |      0.2446 |
| prophet              |     87 |         0.121  | 0.3713 |  0.5    |  0.8496 |                 0.0993 |      0.2481 |      0.0737 |
| har_seasonal         |     87 |         0.1219 | 0.3854 |  0.4454 |  0.8731 |                 0.1008 |      0.2248 |      0.1609 |
| har                  |     87 |         0.1248 | 0.3946 |  0.4737 |  0.8784 |                 0.0902 |      0.228  |      0.1489 |
| persistence          |     87 |         0.1383 | 0.4345 |  0.5235 |  0.9133 |                 0      |      0.2679 |      0      |
| seasonal_persistence |     87 |         0.154  | 0.4755 |  0.4756 |  0.8721 |                -0.1447 |      0.3093 |     -0.1548 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 7 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0996.

Matched on the 84 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.36) and 0.40 on the day-level error (0.23 to 0.57). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

