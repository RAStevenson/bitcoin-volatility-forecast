# Daily record (generated)

Forecast days scored: 62. Resolved rows: 11832. Pending (logged, outcome not yet observed): 192.

Every row from an earlier run was committed to git before its target hour completed. Any exceptions and their reasons are listed below. Each run audits every earlier commit of the forecast log, so a day's rows are checked on the run after the one that committed them. The commit history is the timestamp evidence.

- The 2026-09-03 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-09-04 05:15 UTC, 17 hours after its first target hour completed. The machine that ran the daily job had an unplanned restart.
- The 2026-10-02 forecast, made from data through the hour starting 10:00 UTC (8 models), was first committed at 2026-10-02 16:40 UTC, 5 hours after its first target hour completed. The run that committed it was started by GitHub's scheduled trigger at 16:38 UTC.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     59 |         0.1012 | 0.3148 |  0.4965 |  0.8955 |                 0.2307 |      0.172  |      0.4177 |
| gbm                  |     62 |         0.1082 | 0.334  |  0.4496 |  0.8421 |                 0.1844 |      0.1792 |      0.3774 |
| sarima               |     62 |         0.1136 | 0.3504 |  0.5659 |  0.9106 |                 0.143  |      0.2017 |      0.2993 |
| har_seasonal         |     62 |         0.1245 | 0.3915 |  0.4449 |  0.8656 |                 0.0597 |      0.2528 |      0.1219 |
| har                  |     62 |         0.1277 | 0.4016 |  0.4745 |  0.8663 |                 0.0466 |      0.2624 |      0.0885 |
| prophet              |     62 |         0.1308 | 0.3953 |  0.4798 |  0.8226 |                 0.0031 |      0.3023 |     -0.0502 |
| persistence          |     62 |         0.1351 | 0.4222 |  0.5383 |  0.9187 |                 0      |      0.2879 |      0      |
| seasonal_persistence |     62 |         0.1585 | 0.4856 |  0.4751 |  0.8636 |                -0.2057 |      0.3097 |     -0.0756 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

Matched on the 59 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.26 on the hourly pinball loss (95% interval 0.18 to 0.34) and 0.42 on the day-level error (0.21 to 0.62). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

The calibration check flags these models, whose average coverage has sat farther from 0.90 than day-to-day spread would explain on 3 consecutive scored days: gbm, coverage 0.8421, p-value 0.0044. Bands are left as each model produces them, and the coverage column is the record of that. A model's 90% band is meant to contain the realized value on about 90% of hours. Coverage is the share of hours that landed inside it. The check takes that share for each day a model has been scored, one number per day. It asks whether the average of those numbers sits farther from 0.90 than their day-to-day spread would explain, in either direction (a two-sided t-test). The p-value is the chance of an average at least that far from 0.90 if the model's true coverage were exactly 0.90. Because 8 models are tested at once, each is held to a threshold of 0.05 divided by 8, or 0.0063, so that the chance of a false alarm across all of them stays at or below 5% (a Bonferroni correction). A p-value below that threshold is a rejection. A model is flagged only after it is rejected on 3 consecutive scored days, so one noisy day cannot raise an alarm.

