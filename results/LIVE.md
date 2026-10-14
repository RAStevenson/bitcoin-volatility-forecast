# Daily record (generated)

Forecast days scored: 71. Resolved rows: 13560. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     68 |         0.1    | 0.3126 |  0.4939 |  0.8964 |                 0.244  |      0.1676 |      0.4228 |
| gbm                  |     71 |         0.1072 | 0.3315 |  0.4448 |  0.8457 |                 0.1976 |      0.174  |      0.3875 |
| sarima               |     71 |         0.1128 | 0.349  |  0.5663 |  0.9137 |                 0.1533 |      0.2005 |      0.2941 |
| har_seasonal         |     71 |         0.1239 | 0.3904 |  0.4431 |  0.8668 |                 0.0698 |      0.2481 |      0.1267 |
| har                  |     71 |         0.1267 | 0.3995 |  0.4724 |  0.8685 |                 0.0592 |      0.2587 |      0.0893 |
| prophet              |     71 |         0.1274 | 0.3888 |  0.48   |  0.8316 |                 0.036  |      0.2837 |      0.0013 |
| persistence          |     71 |         0.1358 | 0.4248 |  0.5335 |  0.9149 |                 0      |      0.2841 |      0      |
| seasonal_persistence |     71 |         0.1579 | 0.4856 |  0.4701 |  0.8633 |                -0.1929 |      0.3101 |     -0.0917 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 68 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.18 to 0.36) and 0.42 on the day-level error (0.22 to 0.62). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

