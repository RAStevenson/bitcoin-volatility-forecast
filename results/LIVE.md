# Daily record (generated)

Forecast days scored: 52. Resolved rows: 9912. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed, except the forecast day listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     49 |         0.1023 | 0.3193 |  0.4957 |  0.9014 |                 0.2269 |      0.1887 |      0.3981 |
| gbm                  |     52 |         0.1092 | 0.3365 |  0.4503 |  0.8389 |                 0.1805 |      0.1961 |      0.3543 |
| sarima               |     52 |         0.1132 | 0.3469 |  0.5761 |  0.9111 |                 0.1506 |      0.2018 |      0.3352 |
| har_seasonal         |     52 |         0.123  | 0.3849 |  0.4591 |  0.8694 |                 0.0754 |      0.2553 |      0.1592 |
| har                  |     52 |         0.1262 | 0.3955 |  0.4864 |  0.8734 |                 0.0629 |      0.2647 |      0.1282 |
| persistence          |     52 |         0.1361 | 0.423  |  0.5409 |  0.9135 |                 0      |      0.3036 |      0      |
| prophet              |     52 |         0.1362 | 0.4091 |  0.4704 |  0.8093 |                -0.0367 |      0.3392 |     -0.1173 |
| seasonal_persistence |     52 |         0.1554 | 0.4759 |  0.4832 |  0.871  |                -0.1753 |      0.2932 |      0.0343 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 49 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.16 to 0.35) and 0.40 on the day-level error (0.18 to 0.62). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](fig_live_daily.png)

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 52 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

