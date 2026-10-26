# Daily record (generated)

Forecast days scored: 83. Resolved rows: 15864. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     80 |         0.0996 | 0.3117 |  0.4969 |  0.8969 |                 0.2465 |      0.1547 |      0.3868 |
| gbm                  |     83 |         0.1059 | 0.329  |  0.4518 |  0.8514 |                 0.2066 |      0.1645 |      0.3515 |
| sarima               |     83 |         0.1106 | 0.3415 |  0.5763 |  0.9202 |                 0.1671 |      0.1989 |      0.2163 |
| har_seasonal         |     83 |         0.1216 | 0.3846 |  0.4448 |  0.8735 |                 0.0845 |      0.2197 |      0.1339 |
| prophet              |     83 |         0.122  | 0.3742 |  0.496  |  0.8474 |                 0.0749 |      0.2507 |      0.012  |
| har                  |     83 |         0.1245 | 0.3939 |  0.4734 |  0.878  |                 0.0742 |      0.2234 |      0.1197 |
| persistence          |     83 |         0.1357 | 0.4252 |  0.5331 |  0.9162 |                 0      |      0.2537 |      0      |
| seasonal_persistence |     83 |         0.1546 | 0.477  |  0.4784 |  0.87   |                -0.1718 |      0.3137 |     -0.2364 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 3 forecast days scored since the change, gbm leads with a mean pinball loss of 0.0991.

Matched on the 80 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.20 to 0.35) and 0.39 on the day-level error (0.20 to 0.57). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

