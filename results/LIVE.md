# Daily record (generated)

Forecast days scored: 73. Resolved rows: 13944. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     70 |         0.1    | 0.3129 |  0.4911 |  0.8964 |                 0.243  |      0.1705 |      0.4142 |
| gbm                  |     73 |         0.1072 | 0.3316 |  0.4463 |  0.847  |                 0.1963 |      0.1761 |      0.3818 |
| sarima               |     73 |         0.1126 | 0.3478 |  0.5696 |  0.915  |                 0.1535 |      0.2037 |      0.285  |
| har_seasonal         |     73 |         0.1238 | 0.39   |  0.4446 |  0.867  |                 0.0692 |      0.251  |      0.1187 |
| har                  |     73 |         0.1266 | 0.3986 |  0.476  |  0.8699 |                 0.0597 |      0.2625 |      0.0786 |
| prophet              |     73 |         0.1266 | 0.3864 |  0.4823 |  0.8328 |                 0.0403 |      0.2807 |      0.0145 |
| persistence          |     73 |         0.1357 | 0.4243 |  0.5365 |  0.9161 |                 0      |      0.2849 |      0      |
| seasonal_persistence |     73 |         0.1571 | 0.4834 |  0.472  |  0.8653 |                -0.1888 |      0.3095 |     -0.0864 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 70 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.19 to 0.35) and 0.41 on the day-level error (0.22 to 0.61). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

