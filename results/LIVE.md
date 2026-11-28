# Daily record (generated)

Forecast days scored: 116. Resolved rows: 22200. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    113 |         0.1055 | 0.3276 |  0.4742 |  0.8698 |                 0.2338 |      0.1861 |      0.3342 |
| gbm                  |    116 |         0.1083 | 0.3352 |  0.4357 |  0.8373 |                 0.2199 |      0.1851 |      0.3383 |
| sarima               |    116 |         0.1158 | 0.3594 |  0.5539 |  0.9088 |                 0.1619 |      0.2245 |      0.1974 |
| har_seasonal         |    116 |         0.1233 | 0.3897 |  0.4472 |  0.8696 |                 0.1115 |      0.2353 |      0.1591 |
| har                  |    116 |         0.1263 | 0.3999 |  0.4777 |  0.8746 |                 0.1012 |      0.239  |      0.1458 |
| prophet              |    116 |         0.1266 | 0.386  |  0.4943 |  0.8445 |                 0.0763 |      0.2693 |      0.0376 |
| persistence          |    116 |         0.1417 | 0.4439 |  0.5233 |  0.9045 |                 0      |      0.2798 |      0      |
| seasonal_persistence |    116 |         0.1554 | 0.48   |  0.4677 |  0.8703 |                -0.1336 |      0.3182 |     -0.1373 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 36 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1133.

Matched on the 113 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.20 to 0.32) and 0.33 on the day-level error (0.19 to 0.47). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

