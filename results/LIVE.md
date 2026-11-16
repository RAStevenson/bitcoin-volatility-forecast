# Daily record (generated)

Forecast days scored: 104. Resolved rows: 19896. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    101 |         0.1044 | 0.3248 |  0.4806 |  0.8812 |                 0.2443 |      0.183  |      0.3459 |
| gbm                  |    104 |         0.1081 | 0.3345 |  0.4459 |  0.8429 |                 0.224  |      0.1822 |      0.3493 |
| sarima               |    104 |         0.1151 | 0.356  |  0.5609 |  0.9123 |                 0.171  |      0.2217 |      0.2083 |
| prophet              |    104 |         0.1244 | 0.3796 |  0.4968 |  0.8462 |                 0.0962 |      0.26   |      0.0714 |
| har_seasonal         |    104 |         0.1246 | 0.3936 |  0.4399 |  0.865  |                 0.105  |      0.2416 |      0.1373 |
| har                  |    104 |         0.1274 | 0.4033 |  0.4679 |  0.8706 |                 0.0953 |      0.2452 |      0.1244 |
| persistence          |    104 |         0.1421 | 0.4447 |  0.5212 |  0.9038 |                 0      |      0.28   |      0      |
| seasonal_persistence |    104 |         0.1586 | 0.4896 |  0.4607 |  0.8634 |                -0.1534 |      0.3291 |     -0.1753 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 24 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1147.

Matched on the 101 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.20 to 0.34) and 0.35 on the day-level error (0.19 to 0.50). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

