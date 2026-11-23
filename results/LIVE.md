# Daily record (generated)

Forecast days scored: 111. Resolved rows: 21240. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    108 |         0.1047 | 0.3252 |  0.478  |  0.8735 |                 0.24   |      0.1819 |      0.3514 |
| gbm                  |    111 |         0.1082 | 0.3347 |  0.4426 |  0.8412 |                 0.2213 |      0.1853 |      0.34   |
| sarima               |    111 |         0.1159 | 0.3594 |  0.5559 |  0.908  |                 0.1619 |      0.2252 |      0.1977 |
| har_seasonal         |    111 |         0.1235 | 0.3902 |  0.4467 |  0.8682 |                 0.1098 |      0.2371 |      0.1554 |
| har                  |    111 |         0.1264 | 0.3998 |  0.476  |  0.8735 |                 0.1    |      0.2408 |      0.1424 |
| prophet              |    111 |         0.1273 | 0.3869 |  0.494  |  0.842  |                 0.0725 |      0.2703 |      0.0372 |
| persistence          |    111 |         0.1417 | 0.4439 |  0.5218 |  0.905  |                 0      |      0.2807 |      0      |
| seasonal_persistence |    111 |         0.1563 | 0.4827 |  0.4658 |  0.8682 |                -0.139  |      0.3217 |     -0.146  |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 31 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1134.

Matched on the 108 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.20 to 0.33) and 0.35 on the day-level error (0.21 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

