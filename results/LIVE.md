# Daily record (generated)

Forecast days scored: 75. Resolved rows: 14328. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.
- The 2026-10-17 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-17 14:14 UTC, 2 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:12 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     72 |         0.1001 | 0.3131 |  0.4954 |  0.8958 |                 0.2436 |      0.174  |      0.3997 |
| gbm                  |     75 |         0.1072 | 0.3315 |  0.4461 |  0.8483 |                 0.1985 |      0.1782 |      0.3725 |
| sarima               |     75 |         0.1127 | 0.3486 |  0.5683 |  0.915  |                 0.1555 |      0.199  |      0.2992 |
| har_seasonal         |     75 |         0.1238 | 0.3908 |  0.4411 |  0.8661 |                 0.0713 |      0.2473 |      0.129  |
| prophet              |     75 |         0.1258 | 0.3839 |  0.4856 |  0.8344 |                 0.0496 |      0.2752 |      0.0308 |
| har                  |     75 |         0.1268 | 0.4002 |  0.4694 |  0.8706 |                 0.06   |      0.2585 |      0.0896 |
| persistence          |     75 |         0.1361 | 0.4265 |  0.5328 |  0.9161 |                 0      |      0.284  |      0      |
| seasonal_persistence |     75 |         0.158  | 0.4869 |  0.4678 |  0.8639 |                -0.1935 |      0.3097 |     -0.0907 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 72 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.19 to 0.35) and 0.40 on the day-level error (0.21 to 0.59). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

