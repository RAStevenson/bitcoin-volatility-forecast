# Daily record (generated)

Forecast days scored: 79. Resolved rows: 15096. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed, except on the days listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.
- The 2026-10-17 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-17 14:14 UTC, 2 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:12 UTC.
- The 2026-10-18 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-18 14:35 UTC, 3 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 14:33 UTC.
- The 2026-10-19 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-19 17:29 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 17:28 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     76 |         0.0994 | 0.3111 |  0.4973 |  0.8986 |                 0.2506 |      0.1552 |      0.3923 |
| gbm                  |     79 |         0.1065 | 0.33   |  0.4499 |  0.8492 |                 0.2054 |      0.1648 |      0.3581 |
| sarima               |     79 |         0.1112 | 0.3435 |  0.5754 |  0.9182 |                 0.1666 |      0.2046 |      0.2032 |
| har_seasonal         |     79 |         0.1223 | 0.3861 |  0.4462 |  0.8703 |                 0.0843 |      0.2244 |      0.1262 |
| prophet              |     79 |         0.1234 | 0.3778 |  0.4926 |  0.8428 |                 0.068  |      0.2557 |      0.0043 |
| har                  |     79 |         0.1252 | 0.3954 |  0.4752 |  0.875  |                 0.0732 |      0.2286 |      0.1099 |
| persistence          |     79 |         0.1363 | 0.4274 |  0.5306 |  0.9161 |                 0      |      0.2568 |      0      |
| seasonal_persistence |     79 |         0.1559 | 0.4809 |  0.472  |  0.8687 |                -0.1765 |      0.3185 |     -0.2403 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The model settings changed on 2026-10-23. No forecast day made on the current settings has resolved yet, so every row above is from the settings before the change.

Matched on the 76 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.20 to 0.36) and 0.39 on the day-level error (0.20 to 0.58). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

