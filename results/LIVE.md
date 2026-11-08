# Daily record (generated)

Forecast days scored: 96. Resolved rows: 18360. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     93 |         0.1006 | 0.3144 |  0.4884 |  0.8875 |                 0.2497 |      0.1672 |      0.3702 |
| gbm                  |     96 |         0.1064 | 0.3305 |  0.4453 |  0.8481 |                 0.2143 |      0.1742 |      0.3458 |
| sarima               |     96 |         0.1121 | 0.3474 |  0.5664 |  0.9193 |                 0.169  |      0.2133 |      0.1987 |
| prophet              |     96 |         0.1185 | 0.3644 |  0.5078 |  0.8568 |                 0.1148 |      0.2448 |      0.0805 |
| har_seasonal         |     96 |         0.1224 | 0.3883 |  0.4375 |  0.8702 |                 0.0941 |      0.2312 |      0.1318 |
| har                  |     96 |         0.1259 | 0.3989 |  0.467  |  0.8741 |                 0.0804 |      0.2345 |      0.1193 |
| persistence          |     96 |         0.1381 | 0.4347 |  0.523  |  0.9145 |                 0      |      0.2662 |      0      |
| seasonal_persistence |     96 |         0.1567 | 0.4848 |  0.464  |  0.8685 |                -0.1692 |      0.3246 |     -0.2193 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 16 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0967.

Matched on the 93 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.37 on the day-level error (0.21 to 0.53). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

