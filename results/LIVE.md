# Daily record (generated)

Forecast days scored: 110. Resolved rows: 21048. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    107 |         0.1047 | 0.3252 |  0.4794 |  0.8746 |                 0.2394 |      0.1826 |      0.3444 |
| gbm                  |    110 |         0.1083 | 0.3353 |  0.4424 |  0.8417 |                 0.22   |      0.186  |      0.3329 |
| sarima               |    110 |         0.116  | 0.3591 |  0.5572 |  0.9087 |                 0.1611 |      0.2259 |      0.1898 |
| har_seasonal         |    110 |         0.1237 | 0.3905 |  0.447  |  0.8678 |                 0.1087 |      0.2378 |      0.1472 |
| har                  |    110 |         0.1267 | 0.401  |  0.4739 |  0.8727 |                 0.0979 |      0.2418 |      0.133  |
| prophet              |    110 |         0.1274 | 0.3871 |  0.4936 |  0.8413 |                 0.0712 |      0.2705 |      0.0299 |
| persistence          |    110 |         0.1417 | 0.4438 |  0.5227 |  0.9049 |                 0      |      0.2789 |      0      |
| seasonal_persistence |    110 |         0.1564 | 0.4828 |  0.4659 |  0.8674 |                -0.1412 |      0.3216 |     -0.1533 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 30 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1141.

Matched on the 107 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.20 to 0.33) and 0.34 on the day-level error (0.20 to 0.49). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

