# Daily record (generated)

Forecast days scored: 101. Resolved rows: 19320. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     98 |         0.1014 | 0.3163 |  0.4881 |  0.8873 |                 0.2596 |      0.1736 |      0.3699 |
| gbm                  |    101 |         0.107  | 0.3315 |  0.4472 |  0.8449 |                 0.2261 |      0.1783 |      0.354  |
| sarima               |    101 |         0.1134 | 0.351  |  0.5648 |  0.9163 |                 0.1771 |      0.2172 |      0.2127 |
| prophet              |    101 |         0.1186 | 0.3646 |  0.507  |  0.8564 |                 0.1326 |      0.2433 |      0.1181 |
| har_seasonal         |    101 |         0.1235 | 0.3906 |  0.4414 |  0.8672 |                 0.1058 |      0.2372 |      0.1403 |
| har                  |    101 |         0.1268 | 0.4013 |  0.467  |  0.8725 |                 0.0937 |      0.2409 |      0.1272 |
| persistence          |    101 |         0.1411 | 0.4421 |  0.5215 |  0.9068 |                 0      |      0.2759 |      0      |
| seasonal_persistence |    101 |         0.1591 | 0.4907 |  0.4612 |  0.8626 |                -0.163  |      0.3274 |     -0.1866 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 21 forecast days scored since the change, prophet leads with a mean pinball loss of 0.1022.

Matched on the 98 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.29 on the hourly pinball loss (95% interval 0.22 to 0.36) and 0.37 on the day-level error (0.21 to 0.53). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

