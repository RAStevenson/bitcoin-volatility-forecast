# Daily record (generated)

Forecast days scored: 81. Resolved rows: 15480. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     78 |         0.0991 | 0.3102 |  0.5005 |  0.899  |                 0.2495 |      0.1558 |      0.3846 |
| gbm                  |     81 |         0.106  | 0.3293 |  0.4506 |  0.8519 |                 0.2058 |      0.1645 |      0.3539 |
| sarima               |     81 |         0.1104 | 0.34   |  0.5808 |  0.9203 |                 0.1688 |      0.2001 |      0.2142 |
| har_seasonal         |     81 |         0.1215 | 0.3838 |  0.447  |  0.8729 |                 0.0859 |      0.2205 |      0.134  |
| prophet              |     81 |         0.1224 | 0.3751 |  0.4959 |  0.8462 |                 0.0715 |      0.2532 |      0.0056 |
| har                  |     81 |         0.1246 | 0.3937 |  0.4753 |  0.8776 |                 0.0744 |      0.2242 |      0.1193 |
| persistence          |     81 |         0.1358 | 0.4251 |  0.5329 |  0.9167 |                 0      |      0.2546 |      0      |
| seasonal_persistence |     81 |         0.1543 | 0.4754 |  0.4784 |  0.8719 |                -0.1692 |      0.3152 |     -0.2381 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 1 forecast days scored since the change, sarima leads with a mean pinball loss of 0.0869.

Matched on the 78 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.20 to 0.35) and 0.38 on the day-level error (0.20 to 0.57). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

