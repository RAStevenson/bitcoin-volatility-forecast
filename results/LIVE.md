# Live scoreboard (generated)

Forecast days scored: 42. Resolved rows: 7992. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     39 |         0.1059 | 0.3285 |  0.485  |  0.8932 |                 0.2276 |
| gbm                  |     42 |         0.1127 | 0.3458 |  0.4315 |  0.8244 |                 0.183  |
| sarima               |     42 |         0.1183 | 0.3668 |  0.5486 |  0.8968 |                 0.1457 |
| har_seasonal         |     42 |         0.1286 | 0.4017 |  0.4474 |  0.8542 |                 0.0678 |
| har                  |     42 |         0.1316 | 0.4122 |  0.4722 |  0.8581 |                 0.0572 |
| persistence          |     42 |         0.141  | 0.4395 |  0.5198 |  0.9028 |                 0      |
| prophet              |     42 |         0.1447 | 0.4334 |  0.4405 |  0.7857 |                -0.0677 |
| seasonal_persistence |     42 |         0.1639 | 0.503  |  0.4573 |  0.8562 |                -0.1972 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 42 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

