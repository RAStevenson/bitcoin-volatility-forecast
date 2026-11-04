# Daily record (generated)

Forecast days scored: 92. Resolved rows: 17592. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     89 |         0.0997 | 0.3121 |  0.4939 |  0.8947 |                 0.2564 |      0.1636 |      0.3882 |
| gbm                  |     92 |         0.1056 | 0.3273 |  0.4524 |  0.8496 |                 0.2203 |      0.1693 |      0.3685 |
| sarima               |     92 |         0.1106 | 0.3415 |  0.5756 |  0.9226 |                 0.1797 |      0.2059 |      0.232  |
| prophet              |     92 |         0.1192 | 0.3661 |  0.5059 |  0.8537 |                 0.1083 |      0.2452 |      0.0856 |
| har_seasonal         |     92 |         0.1214 | 0.3847 |  0.4438 |  0.8745 |                 0.1009 |      0.2257 |      0.1583 |
| har                  |     92 |         0.1244 | 0.394  |  0.4728 |  0.88   |                 0.09   |      0.2288 |      0.1466 |
| persistence          |     92 |         0.1379 | 0.4342 |  0.5222 |  0.9153 |                 0      |      0.2681 |      0      |
| seasonal_persistence |     92 |         0.1554 | 0.4806 |  0.4692 |  0.8705 |                -0.1605 |      0.3156 |     -0.1771 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 12 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0952.

Matched on the 89 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.39 on the day-level error (0.23 to 0.55). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

