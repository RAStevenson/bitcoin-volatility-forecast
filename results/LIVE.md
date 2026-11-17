# Daily record (generated)

Forecast days scored: 105. Resolved rows: 20088. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    102 |         0.1038 | 0.3229 |  0.4841 |  0.8819 |                 0.2455 |      0.1813 |      0.3478 |
| gbm                  |    105 |         0.1077 | 0.3333 |  0.4464 |  0.844  |                 0.2243 |      0.1818 |      0.3471 |
| sarima               |    105 |         0.1147 | 0.3548 |  0.5635 |  0.9131 |                 0.1709 |      0.2209 |      0.2068 |
| prophet              |    105 |         0.1239 | 0.3781 |  0.5    |  0.8472 |                 0.0967 |      0.259  |      0.0698 |
| har_seasonal         |    105 |         0.124  | 0.3915 |  0.444  |  0.8659 |                 0.1061 |      0.2395 |      0.1399 |
| har                  |    105 |         0.127  | 0.4015 |  0.471  |  0.8714 |                 0.096  |      0.2431 |      0.1267 |
| persistence          |    105 |         0.1417 | 0.443  |  0.5234 |  0.9044 |                 0      |      0.2784 |      0      |
| seasonal_persistence |    105 |         0.1579 | 0.4873 |  0.4627 |  0.8647 |                -0.1521 |      0.3279 |     -0.1777 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 25 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1127.

Matched on the 102 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.35 on the day-level error (0.20 to 0.50). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

