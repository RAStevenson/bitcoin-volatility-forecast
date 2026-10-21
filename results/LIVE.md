# Daily record (generated)

Forecast days scored: 78. Resolved rows: 14904. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed, except on the days listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.
- The 2026-10-17 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-17 14:14 UTC, 2 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:12 UTC.
- The 2026-10-18 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-18 14:35 UTC, 3 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:33 UTC.
- The 2026-10-19 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-19 17:29 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 17:28 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     75 |         0.0998 | 0.3122 |  0.4972 |  0.8972 |                 0.2506 |      0.1728 |      0.4211 |
| gbm                  |     78 |         0.1068 | 0.3309 |  0.4482 |  0.8478 |                 0.206  |      0.1753 |      0.4004 |
| sarima               |     78 |         0.1117 | 0.3451 |  0.5726 |  0.9172 |                 0.1666 |      0.1976 |      0.3242 |
| har_seasonal         |     78 |         0.1227 | 0.3875 |  0.4434 |  0.8691 |                 0.0843 |      0.2427 |      0.1702 |
| prophet              |     78 |         0.1241 | 0.3797 |  0.4893 |  0.8408 |                 0.0666 |      0.266  |      0.0904 |
| har                  |     78 |         0.1257 | 0.3971 |  0.4717 |  0.8734 |                 0.0727 |      0.2549 |      0.1282 |
| persistence          |     78 |         0.1367 | 0.4292 |  0.5278 |  0.9156 |                 0      |      0.2924 |      0      |
| seasonal_persistence |     78 |         0.1567 | 0.4837 |  0.4696 |  0.867  |                -0.1782 |      0.3051 |     -0.0434 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 75 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.20 to 0.36) and 0.42 on the day-level error (0.24 to 0.60). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

