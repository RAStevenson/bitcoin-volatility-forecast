# Live scoreboard (generated)

Forecast days scored: 43. Resolved rows: 8184. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     40 |         0.1054 | 0.3273 |  0.4854 |  0.8948 |                 0.2276 |
| gbm                  |     43 |         0.1123 | 0.3452 |  0.436  |  0.8256 |                 0.1829 |
| sarima               |     43 |         0.1179 | 0.3643 |  0.5543 |  0.8983 |                 0.1446 |
| har_seasonal         |     43 |         0.1283 | 0.4007 |  0.4486 |  0.8566 |                 0.0674 |
| har                  |     43 |         0.1316 | 0.4119 |  0.4748 |  0.8576 |                 0.0538 |
| persistence          |     43 |         0.1404 | 0.4374 |  0.5233 |  0.9041 |                 0      |
| prophet              |     43 |         0.1441 | 0.4316 |  0.4438 |  0.7878 |                -0.0673 |
| seasonal_persistence |     43 |         0.1624 | 0.4982 |  0.4632 |  0.8585 |                -0.1903 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 43 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

