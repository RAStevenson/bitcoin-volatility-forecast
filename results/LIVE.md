# Daily record (generated)

Forecast days scored: 50. Resolved rows: 9528. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed, except the forecast day listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     47 |         0.1031 | 0.3211 |  0.4929 |  0.9016 |                 0.2261 |      0.1888 |      0.4051 |
| gbm                  |     50 |         0.11   | 0.339  |  0.4425 |  0.8367 |                 0.18   |      0.2019 |      0.3418 |
| sarima               |     50 |         0.1145 | 0.3518 |  0.5692 |  0.9083 |                 0.148  |      0.2046 |      0.3331 |
| har_seasonal         |     50 |         0.1242 | 0.3887 |  0.4542 |  0.8667 |                 0.0733 |      0.2605 |      0.1509 |
| har                  |     50 |         0.1273 | 0.399  |  0.4825 |  0.87   |                 0.0612 |      0.2707 |      0.1175 |
| persistence          |     50 |         0.137  | 0.4262 |  0.5367 |  0.9117 |                 0      |      0.3068 |      0      |
| prophet              |     50 |         0.1386 | 0.4164 |  0.4608 |  0.8042 |                -0.049  |      0.3494 |     -0.139  |
| seasonal_persistence |     50 |         0.1582 | 0.4857 |  0.4725 |  0.8658 |                -0.1891 |      0.3029 |      0.0127 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 47 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.16 to 0.36) and 0.41 on the day-level error (0.18 to 0.63). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](fig_live_daily.png)

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 50 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

