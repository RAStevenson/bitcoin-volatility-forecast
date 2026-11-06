# Daily record (generated)

Forecast days scored: 94. Resolved rows: 17976. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     91 |         0.0999 | 0.3127 |  0.4913 |  0.891  |                 0.2563 |      0.1646 |      0.3903 |
| gbm                  |     94 |         0.1058 | 0.328  |  0.4499 |  0.8506 |                 0.221  |      0.171  |      0.3682 |
| sarima               |     94 |         0.1112 | 0.3436 |  0.5727 |  0.9207 |                 0.1768 |      0.2091 |      0.2271 |
| prophet              |     94 |         0.1189 | 0.3652 |  0.508  |  0.8551 |                 0.1128 |      0.2451 |      0.0943 |
| har_seasonal         |     94 |         0.1215 | 0.3847 |  0.4433 |  0.8746 |                 0.1031 |      0.2277 |      0.1586 |
| har                  |     94 |         0.1246 | 0.3947 |  0.473  |  0.8799 |                 0.0912 |      0.231  |      0.1464 |
| persistence          |     94 |         0.1383 | 0.4354 |  0.5217 |  0.9145 |                 0      |      0.2706 |      0      |
| seasonal_persistence |     94 |         0.1548 | 0.4794 |  0.469  |  0.8723 |                -0.1534 |      0.3135 |     -0.1587 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 14 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0964.

Matched on the 91 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.39 on the day-level error (0.23 to 0.55). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

