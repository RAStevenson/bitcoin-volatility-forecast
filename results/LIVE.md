# Daily record (generated)

Forecast days scored: 61. Resolved rows: 11640. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     58 |         0.101  | 0.3143 |  0.4957 |  0.8951 |                 0.2318 |      0.1748 |      0.4062 |
| gbm                  |     61 |         0.1086 | 0.335  |  0.4495 |  0.8408 |                 0.1815 |      0.1802 |      0.372  |
| sarima               |     61 |         0.1132 | 0.3482 |  0.5697 |  0.9119 |                 0.1456 |      0.2024 |      0.2945 |
| har_seasonal         |     61 |         0.1243 | 0.3905 |  0.4467 |  0.8654 |                 0.0603 |      0.2512 |      0.1246 |
| har                  |     61 |         0.1278 | 0.4017 |  0.4754 |  0.8654 |                 0.0448 |      0.2605 |      0.0923 |
| prophet              |     61 |         0.1309 | 0.3956 |  0.4788 |  0.8231 |                 0.0014 |      0.3056 |     -0.0651 |
| persistence          |     61 |         0.1352 | 0.4217 |  0.5396 |  0.918  |                 0      |      0.2869 |      0      |
| seasonal_persistence |     61 |         0.1569 | 0.4806 |  0.4781 |  0.8675 |                -0.1946 |      0.302  |     -0.0526 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 58 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.18 to 0.35) and 0.41 on the day-level error (0.20 to 0.61). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

The calibration check passes and flags no model. It rejects gbm, coverage 0.8408, p-value 0.0042, day 2 of 3, short of the 3 consecutive days needed to flag it. A model's 90% band is meant to contain the realized value on about 90% of hours. Coverage is the share of hours that landed inside it. The check takes that share for each day a model has been scored, one number per day. It asks whether the average of those numbers sits farther from 0.90 than their day-to-day spread would explain, in either direction (a two-sided t-test). The p-value is the chance of an average at least that far from 0.90 if the model's true coverage were exactly 0.90. Because 8 models are tested at once, each is held to a threshold of 0.05 divided by 8, or 0.0063, so that the chance of a false alarm across all of them stays at or below 5% (a Bonferroni correction). A p-value below that threshold is a rejection. A model is flagged only after it is rejected on 3 consecutive scored days, so one noisy day cannot raise an alarm.

