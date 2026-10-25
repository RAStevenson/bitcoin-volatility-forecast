# Daily record (generated)

Forecast days scored: 82. Resolved rows: 15672. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     79 |         0.0994 | 0.3109 |  0.4995 |  0.8972 |                 0.2469 |      0.1542 |      0.3857 |
| gbm                  |     82 |         0.106  | 0.3291 |  0.4512 |  0.8511 |                 0.2054 |      0.1649 |      0.3465 |
| sarima               |     82 |         0.1105 | 0.3406 |  0.5793 |  0.9197 |                 0.1668 |      0.2005 |      0.2058 |
| har_seasonal         |     82 |         0.1216 | 0.3844 |  0.4446 |  0.873  |                 0.0839 |      0.2202 |      0.1276 |
| prophet              |     82 |         0.1223 | 0.3746 |  0.4964 |  0.846  |                 0.0722 |      0.2535 |     -0.0044 |
| har                  |     82 |         0.1248 | 0.3945 |  0.4731 |  0.877  |                 0.0719 |      0.2238 |      0.1133 |
| persistence          |     82 |         0.1356 | 0.4245 |  0.5335 |  0.9162 |                 0      |      0.2524 |      0      |
| seasonal_persistence |     82 |         0.1541 | 0.4751 |  0.4792 |  0.8725 |                -0.1687 |      0.3156 |     -0.2503 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 2 forecast days scored since the change, prophet leads with a mean pinball loss of 0.1001.

Matched on the 79 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.20 to 0.35) and 0.39 on the day-level error (0.20 to 0.57). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

