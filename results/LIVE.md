# Daily record (generated)

Forecast days scored: 109. Resolved rows: 20856. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    106 |         0.104  | 0.3237 |  0.4819 |  0.8781 |                 0.2443 |      0.1838 |      0.3427 |
| gbm                  |    109 |         0.1081 | 0.3344 |  0.443  |  0.8425 |                 0.2215 |      0.1862 |      0.3346 |
| sarima               |    109 |         0.1158 | 0.3584 |  0.5581 |  0.9102 |                 0.1629 |      0.2258 |      0.1934 |
| har_seasonal         |    109 |         0.1236 | 0.3899 |  0.448  |  0.8681 |                 0.1095 |      0.2391 |      0.1458 |
| prophet              |    109 |         0.1253 | 0.3815 |  0.4973 |  0.8459 |                 0.0864 |      0.2638 |      0.0577 |
| har                  |    109 |         0.1266 | 0.4006 |  0.4748 |  0.8731 |                 0.0986 |      0.243  |      0.132  |
| persistence          |    109 |         0.1417 | 0.4437 |  0.5229 |  0.9048 |                 0      |      0.2799 |      0      |
| seasonal_persistence |    109 |         0.1559 | 0.4811 |  0.4683 |  0.8685 |                -0.1378 |      0.3207 |     -0.1457 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 29 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1134.

Matched on the 106 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.34 on the day-level error (0.20 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

