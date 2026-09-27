# Daily record (generated)

Forecast days scored: 53. Resolved rows: 10104. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     50 |         0.102  | 0.3184 |  0.4958 |  0.9033 |                 0.2317 |      0.1851 |      0.3998 |
| gbm                  |     53 |         0.1092 | 0.3367 |  0.4505 |  0.8412 |                 0.1827 |      0.1933 |      0.3535 |
| sarima               |     53 |         0.1132 | 0.3478 |  0.5708 |  0.9127 |                 0.1528 |      0.1998 |      0.3317 |
| har_seasonal         |     53 |         0.1235 | 0.3873 |  0.4536 |  0.8695 |                 0.0748 |      0.2531 |      0.1535 |
| har                  |     53 |         0.127  | 0.3987 |  0.4811 |  0.8695 |                 0.0602 |      0.2616 |      0.1251 |
| prophet              |     53 |         0.1353 | 0.4064 |  0.4725 |  0.8121 |                -0.026  |      0.3337 |     -0.1161 |
| persistence          |     53 |         0.1364 | 0.4253 |  0.5362 |  0.9151 |                 0      |      0.299  |      0      |
| seasonal_persistence |     53 |         0.155  | 0.4756 |  0.4796 |  0.8726 |                -0.1701 |      0.2918 |      0.0239 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 50 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.17 to 0.36) and 0.40 on the day-level error (0.18 to 0.62). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

The calibration check passes. A model's 90% band is meant to contain the realized value on about 90% of hours. Coverage is the share of hours that landed inside it. The check takes that share for each day a model has been scored, one number per day. It asks whether the average of those numbers sits farther from 0.90 than their day-to-day spread would explain, in either direction (a two-sided t-test). The p-value is the chance of an average at least that far from 0.90 if the model's true coverage were exactly 0.90. Because 8 models are tested at once, each is held to a threshold of 0.05 divided by 8, or 0.0063, so that the chance of a false alarm across all of them stays at or below 5% (a Bonferroni correction). A p-value below that threshold is a rejection. A model is flagged only after it is rejected on 3 consecutive scored days, so one noisy day cannot raise an alarm. No model's average coverage sits farther from 0.90 than its day-to-day spread would explain.

