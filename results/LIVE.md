# Live scoreboard (generated)

Forecast days scored: 17. Resolved rows: 3192. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     14 |         0.1174 | 0.3446 |  0.5208 |  0.8423 |                 0.2371 |
| prophet              |     17 |         0.1306 | 0.395  |  0.4706 |  0.8211 |                 0.1385 |
| gbm                  |     17 |         0.1346 | 0.4007 |  0.3554 |  0.75   |                 0.1283 |
| sarima               |     17 |         0.1406 | 0.4293 |  0.5098 |  0.8186 |                 0.0911 |
| har_seasonal         |     17 |         0.1463 | 0.4437 |  0.4363 |  0.7892 |                 0.0573 |
| har                  |     17 |         0.1511 | 0.4596 |  0.4657 |  0.7966 |                 0.0357 |
| persistence          |     17 |         0.1591 | 0.4834 |  0.5025 |  0.8578 |                 0      |
| seasonal_persistence |     17 |         0.1873 | 0.5545 |  0.4657 |  0.7917 |                -0.2352 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 17 scored days: gbm 0.7500; har 0.7966; har_seasonal 0.7892; seasonal_persistence 0.7917.

