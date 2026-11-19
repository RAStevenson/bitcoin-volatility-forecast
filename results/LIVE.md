# Daily record (generated)

Forecast days scored: 107. Resolved rows: 20472. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    104 |         0.1034 | 0.3216 |  0.4848 |  0.883  |                 0.2463 |      0.1807 |      0.3457 |
| gbm                  |    107 |         0.1071 | 0.3317 |  0.447  |  0.8458 |                 0.2257 |      0.182  |      0.3421 |
| sarima               |    107 |         0.1144 | 0.354  |  0.5639 |  0.9143 |                 0.1698 |      0.2206 |      0.2026 |
| har_seasonal         |    107 |         0.1232 | 0.3887 |  0.4486 |  0.8684 |                 0.1083 |      0.2365 |      0.145  |
| prophet              |    107 |         0.1232 | 0.376  |  0.5016 |  0.8493 |                 0.0982 |      0.2574 |      0.0694 |
| har                  |    107 |         0.1263 | 0.3993 |  0.4762 |  0.8731 |                 0.0972 |      0.2403 |      0.1314 |
| persistence          |    107 |         0.1412 | 0.4412 |  0.5261 |  0.9054 |                 0      |      0.2766 |      0      |
| seasonal_persistence |    107 |         0.1565 | 0.4825 |  0.4681 |  0.8672 |                -0.1463 |      0.3236 |     -0.1696 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 27 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1100.

Matched on the 104 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.35 on the day-level error (0.20 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

