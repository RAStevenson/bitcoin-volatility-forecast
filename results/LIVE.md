# Daily record (generated)

Forecast days scored: 90. Resolved rows: 17208. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     87 |         0.0994 | 0.3112 |  0.4966 |  0.8966 |                 0.2578 |      0.1609 |      0.3933 |
| gbm                  |     90 |         0.1059 | 0.3281 |  0.4532 |  0.8491 |                 0.2179 |      0.1692 |      0.364  |
| sarima               |     90 |         0.1107 | 0.3418 |  0.575  |  0.9218 |                 0.1786 |      0.2056 |      0.227  |
| prophet              |     90 |         0.12   | 0.3685 |  0.5028 |  0.8519 |                 0.1028 |      0.2484 |      0.0663 |
| har_seasonal         |     90 |         0.1215 | 0.3843 |  0.4454 |  0.8741 |                 0.0997 |      0.2246 |      0.1555 |
| har                  |     90 |         0.1245 | 0.394  |  0.4718 |  0.8787 |                 0.088  |      0.2276 |      0.1442 |
| persistence          |     90 |         0.1378 | 0.4333 |  0.5241 |  0.9148 |                 0      |      0.266  |      0      |
| seasonal_persistence |     90 |         0.1557 | 0.4815 |  0.4685 |  0.8704 |                -0.1634 |      0.3187 |     -0.1982 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 10 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0969.

Matched on the 87 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.36) and 0.39 on the day-level error (0.23 to 0.56). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

