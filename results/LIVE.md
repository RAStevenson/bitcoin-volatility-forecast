# Daily record (generated)

Forecast days scored: 77. Resolved rows: 14712. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.
- The 2026-10-17 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-17 14:14 UTC, 2 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:12 UTC.
- The 2026-10-18 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-18 14:35 UTC, 3 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:33 UTC.
- The 2026-10-19 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-19 17:29 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 17:28 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     74 |         0.0998 | 0.3122 |  0.4983 |  0.897  |                 0.2484 |      0.1727 |      0.4131 |
| gbm                  |     77 |         0.1067 | 0.3305 |  0.4497 |  0.8496 |                 0.2049 |      0.177  |      0.386  |
| sarima               |     77 |         0.1119 | 0.346  |  0.5714 |  0.9172 |                 0.1634 |      0.1967 |      0.3178 |
| har_seasonal         |     77 |         0.123  | 0.3881 |  0.4432 |  0.8685 |                 0.0804 |      0.244  |      0.1538 |
| prophet              |     77 |         0.1245 | 0.3805 |  0.4897 |  0.8387 |                 0.0617 |      0.2694 |      0.0655 |
| har                  |     77 |         0.1259 | 0.3976 |  0.4719 |  0.8728 |                 0.0688 |      0.2559 |      0.1124 |
| persistence          |     77 |         0.1363 | 0.4281 |  0.5281 |  0.9167 |                 0      |      0.2883 |      0      |
| seasonal_persistence |     77 |         0.1576 | 0.4864 |  0.467  |  0.8653 |                -0.1876 |      0.308  |     -0.0684 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 74 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.19 to 0.35) and 0.41 on the day-level error (0.23 to 0.60). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

