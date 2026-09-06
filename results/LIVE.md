# Live scoreboard (generated)

Forecast days scored: 33. Resolved rows: 6264. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     30 |         0.111  | 0.3435 |  0.4708 |  0.8889 |                 0.199  |
| gbm                  |     33 |         0.1179 | 0.361  |  0.4053 |  0.8043 |                 0.1553 |
| sarima               |     33 |         0.1233 | 0.3823 |  0.5328 |  0.8838 |                 0.1178 |
| har_seasonal         |     33 |         0.1335 | 0.4164 |  0.4293 |  0.8371 |                 0.0428 |
| har                  |     33 |         0.1369 | 0.4279 |  0.4609 |  0.846  |                 0.0283 |
| persistence          |     33 |         0.142  | 0.4405 |  0.524  |  0.9028 |                 0      |
| prophet              |     33 |         0.159  | 0.4718 |  0.4015 |  0.7437 |                -0.1651 |
| seasonal_persistence |     33 |         0.166  | 0.5063 |  0.4634 |  0.8497 |                -0.2064 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags day-level 90% coverage away from 0.90 on 3 consecutive scored days: prophet cov90 0.7437, p 0.0054. The test is two-sided on each model's daily coverage against 0.90 over 33 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063). Bands are left as each model produces them, and the coverage column is the honest record of that.

