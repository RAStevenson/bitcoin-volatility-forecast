# Daily record (generated)

Forecast days scored: 76. Resolved rows: 14520. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.
- The 2026-10-17 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-17 14:14 UTC, 2 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:12 UTC.
- The 2026-10-18 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-18 14:35 UTC, 3 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:33 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     73 |         0.1    | 0.3129 |  0.4966 |  0.8973 |                 0.244  |      0.1739 |      0.404  |
| gbm                  |     76 |         0.1069 | 0.3311 |  0.4463 |  0.8503 |                 0.1997 |      0.1783 |      0.3764 |
| sarima               |     76 |         0.1124 | 0.3478 |  0.5691 |  0.9161 |                 0.1563 |      0.1986 |      0.3053 |
| har_seasonal         |     76 |         0.1234 | 0.3894 |  0.4419 |  0.8673 |                 0.0733 |      0.2453 |      0.1421 |
| prophet              |     76 |         0.1251 | 0.3823 |  0.4868 |  0.8366 |                 0.0531 |      0.2718 |      0.0494 |
| har                  |     76 |         0.1263 | 0.399  |  0.4709 |  0.8717 |                 0.062  |      0.2569 |      0.1013 |
| persistence          |     76 |         0.1359 | 0.4262 |  0.5323 |  0.9172 |                 0      |      0.2859 |      0      |
| seasonal_persistence |     76 |         0.1582 | 0.4879 |  0.466  |  0.864  |                -0.1959 |      0.3113 |     -0.0889 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 73 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.19 to 0.35) and 0.40 on the day-level error (0.22 to 0.59). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

