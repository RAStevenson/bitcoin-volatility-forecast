# Daily record (generated)

Forecast days scored: 98. Resolved rows: 18744. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     95 |         0.1014 | 0.3168 |  0.4873 |  0.8868 |                 0.2553 |      0.172  |      0.3712 |
| gbm                  |     98 |         0.1068 | 0.3313 |  0.4456 |  0.8478 |                 0.223  |      0.1775 |      0.3523 |
| sarima               |     98 |         0.1131 | 0.35   |  0.5659 |  0.9175 |                 0.175  |      0.2165 |      0.2101 |
| prophet              |     98 |         0.1191 | 0.3661 |  0.5055 |  0.855  |                 0.1236 |      0.2446 |      0.1075 |
| har_seasonal         |     98 |         0.1234 | 0.3906 |  0.4384 |  0.8682 |                 0.1008 |      0.2361 |      0.1384 |
| har                  |     98 |         0.1266 | 0.4009 |  0.466  |  0.8737 |                 0.0883 |      0.2395 |      0.1262 |
| persistence          |     98 |         0.1402 | 0.4397 |  0.5217 |  0.9103 |                 0      |      0.2741 |      0      |
| seasonal_persistence |     98 |         0.1603 | 0.4944 |  0.4592 |  0.861  |                -0.1789 |      0.3315 |     -0.2096 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 18 forecast days scored since the change, prophet leads with a mean pinball loss of 0.1023.

Matched on the 95 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.37 on the day-level error (0.21 to 0.53). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

