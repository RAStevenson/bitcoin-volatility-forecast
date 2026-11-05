# Daily record (generated)

Forecast days scored: 93. Resolved rows: 17784. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     90 |         0.0996 | 0.3116 |  0.4931 |  0.8931 |                 0.256  |      0.1619 |      0.393  |
| gbm                  |     93 |         0.1054 | 0.3264 |  0.453  |  0.8508 |                 0.2204 |      0.168  |      0.3717 |
| sarima               |     93 |         0.1104 | 0.3406 |  0.5775 |  0.9229 |                 0.1797 |      0.2053 |      0.2326 |
| prophet              |     93 |         0.1188 | 0.3643 |  0.5099 |  0.8548 |                 0.1101 |      0.2434 |      0.0899 |
| har_seasonal         |     93 |         0.1211 | 0.3829 |  0.4467 |  0.875  |                 0.1022 |      0.2246 |      0.1601 |
| har                  |     93 |         0.1241 | 0.3929 |  0.4758 |  0.8804 |                 0.0905 |      0.2279 |      0.148  |
| persistence          |     93 |         0.1377 | 0.4331 |  0.5251 |  0.9153 |                 0      |      0.2675 |      0      |
| seasonal_persistence |     93 |         0.1551 | 0.4801 |  0.4691 |  0.871  |                -0.1608 |      0.3141 |     -0.1744 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 13 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0936.

Matched on the 90 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.39 on the day-level error (0.23 to 0.55). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

