# Daily record (generated)

Forecast days scored: 113. Resolved rows: 21624. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    110 |         0.1046 | 0.3251 |  0.4777 |  0.8735 |                 0.2428 |      0.1832 |      0.3521 |
| gbm                  |    113 |         0.1082 | 0.3348 |  0.4417 |  0.8414 |                 0.2236 |      0.1858 |      0.3433 |
| sarima               |    113 |         0.1161 | 0.3603 |  0.5531 |  0.9082 |                 0.1629 |      0.227  |      0.1978 |
| har_seasonal         |    113 |         0.1235 | 0.3902 |  0.4465 |  0.8691 |                 0.1132 |      0.2378 |      0.1599 |
| har                  |    113 |         0.1264 | 0.3998 |  0.4771 |  0.8743 |                 0.1036 |      0.2415 |      0.1467 |
| prophet              |    113 |         0.1272 | 0.3871 |  0.4937 |  0.8433 |                 0.076  |      0.2711 |      0.0419 |
| persistence          |    113 |         0.1422 | 0.4457 |  0.5195 |  0.9045 |                 0      |      0.283  |      0      |
| seasonal_persistence |    113 |         0.1558 | 0.481  |  0.4679 |  0.8695 |                -0.1325 |      0.3208 |     -0.1335 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 33 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1133.

Matched on the 110 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.33) and 0.35 on the day-level error (0.21 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

