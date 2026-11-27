# Daily record (generated)

Forecast days scored: 115. Resolved rows: 22008. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    112 |         0.1048 | 0.3256 |  0.4766 |  0.8724 |                 0.239  |      0.1852 |      0.3389 |
| gbm                  |    115 |         0.1082 | 0.3348 |  0.4377 |  0.8388 |                 0.221  |      0.185  |      0.3402 |
| sarima               |    115 |         0.1158 | 0.3594 |  0.5543 |  0.9083 |                 0.162  |      0.2262 |      0.1932 |
| har_seasonal         |    115 |         0.1233 | 0.3895 |  0.4478 |  0.8692 |                 0.112  |      0.2373 |      0.1536 |
| har                  |    115 |         0.1262 | 0.3992 |  0.4786 |  0.8746 |                 0.1023 |      0.241  |      0.1403 |
| prophet              |    115 |         0.1268 | 0.3861 |  0.4949 |  0.8442 |                 0.0757 |      0.2709 |      0.0337 |
| persistence          |    115 |         0.1418 | 0.4442 |  0.5228 |  0.9047 |                 0      |      0.2804 |      0      |
| seasonal_persistence |    115 |         0.1555 | 0.4804 |  0.4681 |  0.8699 |                -0.1343 |      0.3203 |     -0.1425 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 35 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1130.

Matched on the 112 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.20 to 0.33) and 0.34 on the day-level error (0.20 to 0.48). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

