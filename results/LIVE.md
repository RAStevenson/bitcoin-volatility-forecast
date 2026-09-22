# Live scoreboard (generated)

Forecast days scored: 49. Resolved rows: 9336. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed, except the forecast day listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     46 |         0.1036 | 0.3228 |  0.4909 |  0.9004 |                 0.2279 |      0.1891 |      0.4076 |
| gbm                  |     49 |         0.1103 | 0.3398 |  0.4413 |  0.8376 |                 0.1844 |      0.2008 |      0.3487 |
| sarima               |     49 |         0.1155 | 0.3557 |  0.5629 |  0.9065 |                 0.1471 |      0.2083 |      0.3245 |
| har_seasonal         |     49 |         0.1251 | 0.3914 |  0.4515 |  0.8648 |                 0.0743 |      0.2625 |      0.1487 |
| har                  |     49 |         0.1283 | 0.4025 |  0.4796 |  0.8673 |                 0.061  |      0.2741 |      0.1112 |
| persistence          |     49 |         0.1379 | 0.4294 |  0.5323 |  0.9099 |                 0      |      0.3084 |      0      |
| prophet              |     49 |         0.1402 | 0.4213 |  0.4541 |  0.8002 |                -0.0534 |      0.3549 |     -0.151  |
| seasonal_persistence |     49 |         0.1594 | 0.489  |  0.4711 |  0.8639 |                -0.1894 |      0.3041 |      0.0139 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 46 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.16 to 0.36) and 0.41 on the day-level error (0.18 to 0.64). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](fig_live_daily.png)

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 49 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

