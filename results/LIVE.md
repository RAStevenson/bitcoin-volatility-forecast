# Daily record (generated)

Forecast days scored: 74. Resolved rows: 14136. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     71 |         0.1    | 0.3127 |  0.4941 |  0.8967 |                 0.2448 |      0.1719 |      0.4017 |
| gbm                  |     74 |         0.1073 | 0.332  |  0.4454 |  0.848  |                 0.198  |      0.1767 |      0.3719 |
| sarima               |     74 |         0.1128 | 0.3492 |  0.567  |  0.915  |                 0.1546 |      0.201  |      0.2857 |
| har_seasonal         |     74 |         0.1239 | 0.3907 |  0.4426 |  0.8677 |                 0.072  |      0.2482 |      0.1181 |
| prophet              |     74 |         0.1262 | 0.3853 |  0.4831 |  0.8339 |                 0.0469 |      0.2775 |      0.0137 |
| har                  |     74 |         0.127  | 0.4006 |  0.4713 |  0.8705 |                 0.0598 |      0.2599 |      0.0765 |
| persistence          |     74 |         0.1361 | 0.4267 |  0.5321 |  0.9161 |                 0      |      0.2814 |      0      |
| seasonal_persistence |     74 |         0.1572 | 0.4844 |  0.4696 |  0.8666 |                -0.1856 |      0.3089 |     -0.0978 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 71 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.19 to 0.36) and 0.40 on the day-level error (0.21 to 0.60). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

