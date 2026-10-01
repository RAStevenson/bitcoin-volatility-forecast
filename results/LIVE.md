# Daily record (generated)

Forecast days scored: 58. Resolved rows: 11064. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     55 |         0.1008 | 0.314  |  0.4955 |  0.9    |                 0.2267 |      0.1821 |      0.3884 |
| gbm                  |     58 |         0.1077 | 0.3321 |  0.454  |  0.8405 |                 0.1796 |      0.1834 |      0.3669 |
| sarima               |     58 |         0.1121 | 0.3444 |  0.5747 |  0.9152 |                 0.1439 |      0.2028 |      0.3002 |
| har_seasonal         |     58 |         0.1228 | 0.3857 |  0.4519 |  0.8693 |                 0.0617 |      0.2501 |      0.1369 |
| har                  |     58 |         0.1258 | 0.3953 |  0.4813 |  0.8714 |                 0.0503 |      0.2599 |      0.1031 |
| prophet              |     58 |         0.1311 | 0.3954 |  0.4792 |  0.8247 |                -0.0119 |      0.3128 |     -0.0798 |
| persistence          |     58 |         0.1339 | 0.4157 |  0.5467 |  0.9188 |                 0      |      0.2897 |      0      |
| seasonal_persistence |     58 |         0.1543 | 0.4737 |  0.4806 |  0.8736 |                -0.1868 |      0.2983 |     -0.0296 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 55 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.17 to 0.34) and 0.39 on the day-level error (0.18 to 0.60). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

The calibration check passes and flags no model. It rejects gbm, coverage 0.8405, p-value 0.0056, day 1 of 3, short of the 3 consecutive days needed to flag it. A model's 90% band is meant to contain the realized value on about 90% of hours. Coverage is the share of hours that landed inside it. The check takes that share for each day a model has been scored, one number per day. It asks whether the average of those numbers sits farther from 0.90 than their day-to-day spread would explain, in either direction (a two-sided t-test). The p-value is the chance of an average at least that far from 0.90 if the model's true coverage were exactly 0.90. Because 8 models are tested at once, each is held to a threshold of 0.05 divided by 8, or 0.0063, so that the chance of a false alarm across all of them stays at or below 5% (a Bonferroni correction). A p-value below that threshold is a rejection. A model is flagged only after it is rejected on 3 consecutive scored days, so one noisy day cannot raise an alarm.

