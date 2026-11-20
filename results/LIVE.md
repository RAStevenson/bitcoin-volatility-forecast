# Daily record (generated)

Forecast days scored: 108. Resolved rows: 20664. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    105 |         0.1033 | 0.3217 |  0.4841 |  0.8825 |                 0.2469 |      0.1814 |      0.3457 |
| gbm                  |    108 |         0.107  | 0.3319 |  0.4448 |  0.8457 |                 0.2267 |      0.183  |      0.3409 |
| sarima               |    108 |         0.1146 | 0.3553 |  0.5602 |  0.9136 |                 0.1685 |      0.222  |      0.2006 |
| har_seasonal         |    108 |         0.123  | 0.3882 |  0.4495 |  0.8688 |                 0.1102 |      0.2366 |      0.148  |
| prophet              |    108 |         0.1231 | 0.3761 |  0.5    |  0.8503 |                 0.0993 |      0.2576 |      0.0722 |
| har                  |    108 |         0.1261 | 0.3987 |  0.4769 |  0.8742 |                 0.0991 |      0.2404 |      0.1343 |
| persistence          |    108 |         0.1412 | 0.4418 |  0.5251 |  0.9059 |                 0      |      0.2777 |      0      |
| seasonal_persistence |    108 |         0.1559 | 0.4806 |  0.4695 |  0.8684 |                -0.1417 |      0.3211 |     -0.1564 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 28 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1095.

Matched on the 105 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.35 on the day-level error (0.20 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

