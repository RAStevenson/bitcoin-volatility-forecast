# Live scoreboard (generated)

Forecast days scored: 44. Resolved rows: 8328. Pending (logged, outcome not yet observed): 240.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     41 |         0.1056 | 0.3277 |  0.4839 |  0.8948 |                 0.2256 |
| gbm                  |     44 |         0.1122 | 0.3449 |  0.435  |  0.8265 |                 0.182  |
| sarima               |     44 |         0.1179 | 0.3633 |  0.5583 |  0.898  |                 0.1433 |
| har_seasonal         |     44 |         0.1277 | 0.3981 |  0.4537 |  0.8581 |                 0.0701 |
| har                  |     44 |         0.1312 | 0.4101 |  0.4775 |  0.859  |                 0.0551 |
| persistence          |     44 |         0.1401 | 0.4363 |  0.5247 |  0.9049 |                 0      |
| prophet              |     44 |         0.1438 | 0.43   |  0.4484 |  0.7896 |                -0.0652 |
| seasonal_persistence |     44 |         0.1609 | 0.4925 |  0.4705 |  0.8611 |                -0.1815 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 44 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

