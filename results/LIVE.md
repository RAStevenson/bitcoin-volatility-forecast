# Daily record (generated)

Forecast days scored: 69. Resolved rows: 13176. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     66 |         0.1002 | 0.3122 |  0.5013 |  0.8958 |                 0.2457 |      0.1661 |      0.4269 |
| gbm                  |     69 |         0.1077 | 0.3328 |  0.4438 |  0.8424 |                 0.1965 |      0.1739 |      0.3864 |
| sarima               |     69 |         0.1133 | 0.3512 |  0.5628 |  0.9124 |                 0.1529 |      0.2006 |      0.2922 |
| har_seasonal         |     69 |         0.1245 | 0.3925 |  0.4408 |  0.8647 |                 0.0681 |      0.2495 |      0.12   |
| har                  |     69 |         0.1275 | 0.4021 |  0.4698 |  0.8653 |                 0.0564 |      0.259  |      0.0862 |
| prophet              |     69 |         0.1286 | 0.3921 |  0.4764 |  0.8279 |                 0.0304 |      0.2898 |     -0.0225 |
| persistence          |     69 |         0.1363 | 0.4264 |  0.5314 |  0.913  |                 0      |      0.2835 |      0      |
| seasonal_persistence |     69 |         0.1584 | 0.4869 |  0.468  |  0.8635 |                -0.1935 |      0.3115 |     -0.0988 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 66 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.18 to 0.36) and 0.43 on the day-level error (0.22 to 0.63). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

The calibration check flags these models, whose average coverage has sat farther from 0.90 than day-to-day spread would explain on 3 consecutive scored days: gbm, coverage 0.8424, p-value 0.0019. Bands are left as each model produces them, and the coverage column is the record of that. A model's 90% band is meant to contain the realized value on about 90% of hours. Coverage is the share of hours that landed inside it. The check takes that share for each day a model has been scored, one number per day. It asks whether the average of those numbers sits farther from 0.90 than their day-to-day spread would explain, in either direction (a two-sided t-test). The p-value is the chance of an average at least that far from 0.90 if the model's true coverage were exactly 0.90. Because 8 models are tested at once, each is held to a threshold of 0.05 divided by 8, or 0.0063, so that the chance of a false alarm across all of them stays at or below 5% (a Bonferroni correction). A p-value below that threshold is a rejection. A model is flagged only after it is rejected on 3 consecutive scored days, so one noisy day cannot raise an alarm.

