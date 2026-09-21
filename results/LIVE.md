# Live scoreboard (generated)

Forecast days scored: 48. Resolved rows: 9144. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed, except the forecast day listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     45 |         0.1042 | 0.3243 |  0.4907 |  0.8991 |                 0.2281 |      0.1898 |      0.4163 |
| gbm                  |     48 |         0.1112 | 0.3418 |  0.441  |  0.8342 |                 0.1832 |      0.2019 |      0.3562 |
| sarima               |     48 |         0.1163 | 0.3588 |  0.5573 |  0.9045 |                 0.1468 |      0.2105 |      0.3288 |
| har_seasonal         |     48 |         0.126  | 0.3941 |  0.4488 |  0.862  |                 0.073  |      0.2669 |      0.1493 |
| har                  |     48 |         0.1292 | 0.4051 |  0.4783 |  0.8646 |                 0.0604 |      0.2773 |      0.116  |
| persistence          |     48 |         0.1388 | 0.4324 |  0.5312 |  0.908  |                 0      |      0.3137 |      0      |
| prophet              |     48 |         0.1409 | 0.4228 |  0.4531 |  0.7995 |                -0.0529 |      0.3548 |     -0.131  |
| seasonal_persistence |     48 |         0.1596 | 0.4899 |  0.4688 |  0.8646 |                -0.1849 |      0.3075 |      0.0196 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 45 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.16 to 0.36) and 0.42 on the day-level error (0.19 to 0.65). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](fig_live_daily.png)

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 48 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

