# Daily record (generated)

Forecast days scored: 56. Resolved rows: 10680. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     53 |         0.1015 | 0.3166 |  0.4953 |  0.9002 |                 0.2239 |      0.1839 |      0.3828 |
| gbm                  |     56 |         0.108  | 0.333  |  0.4546 |  0.8423 |                 0.1806 |      0.187  |      0.3544 |
| sarima               |     56 |         0.1129 | 0.3475 |  0.5699 |  0.9137 |                 0.1422 |      0.2054 |      0.2908 |
| har_seasonal         |     56 |         0.1237 | 0.3886 |  0.4487 |  0.8683 |                 0.0593 |      0.2564 |      0.1147 |
| har                  |     56 |         0.1267 | 0.3983 |  0.4769 |  0.869  |                 0.0473 |      0.2649 |      0.0855 |
| prophet              |     56 |         0.1325 | 0.3986 |  0.4799 |  0.8199 |                -0.018  |      0.321  |     -0.1085 |
| persistence          |     56 |         0.1345 | 0.4181 |  0.5432 |  0.9182 |                 0      |      0.2896 |      0      |
| seasonal_persistence |     56 |         0.1564 | 0.4803 |  0.4754 |  0.869  |                -0.1972 |      0.3029 |     -0.046  |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 53 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.25 on the hourly pinball loss (95% interval 0.16 to 0.35) and 0.38 on the day-level error (0.16 to 0.60). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

The calibration check passes. A model's 90% band is meant to contain the realized value on about 90% of hours. Coverage is the share of hours that landed inside it. The check takes that share for each day a model has been scored, one number per day. It asks whether the average of those numbers sits farther from 0.90 than their day-to-day spread would explain, in either direction (a two-sided t-test). The p-value is the chance of an average at least that far from 0.90 if the model's true coverage were exactly 0.90. Because 8 models are tested at once, each is held to a threshold of 0.05 divided by 8, or 0.0063, so that the chance of a false alarm across all of them stays at or below 5% (a Bonferroni correction). A p-value below that threshold is a rejection. A model is flagged only after it is rejected on 3 consecutive scored days, so one noisy day cannot raise an alarm. No model's average coverage sits farther from 0.90 than its day-to-day spread would explain.

