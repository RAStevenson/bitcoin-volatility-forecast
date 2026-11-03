# Daily record (generated)

Forecast days scored: 91. Resolved rows: 17400. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     88 |         0.0993 | 0.311  |  0.4962 |  0.8968 |                 0.2589 |      0.1619 |      0.3923 |
| gbm                  |     91 |         0.1055 | 0.3272 |  0.4533 |  0.8507 |                 0.2209 |      0.1695 |      0.3655 |
| sarima               |     91 |         0.1105 | 0.3413 |  0.5751 |  0.9226 |                 0.1799 |      0.2055 |      0.2308 |
| prophet              |     91 |         0.1193 | 0.3664 |  0.5055 |  0.8535 |                 0.1076 |      0.2461 |      0.0788 |
| har_seasonal         |     91 |         0.1213 | 0.3841 |  0.4446 |  0.875  |                 0.1015 |      0.2254 |      0.1561 |
| har                  |     91 |         0.1244 | 0.394  |  0.4725 |  0.8791 |                 0.089  |      0.2285 |      0.1446 |
| persistence          |     91 |         0.1378 | 0.4339 |  0.5224 |  0.9153 |                 0      |      0.2671 |      0      |
| seasonal_persistence |     91 |         0.1558 | 0.482  |  0.4684 |  0.869  |                -0.1639 |      0.3191 |     -0.1943 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 11 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0938.

Matched on the 88 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.36) and 0.39 on the day-level error (0.23 to 0.56). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

