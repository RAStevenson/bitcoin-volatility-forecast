# Live scoreboard (generated)

Forecast days scored: 34. Resolved rows: 6456. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     31 |         0.1103 | 0.3423 |  0.4745 |  0.8911 |                 0.2197 |
| gbm                  |     34 |         0.1175 | 0.3608 |  0.4093 |  0.8076 |                 0.1737 |
| sarima               |     34 |         0.1226 | 0.3803 |  0.5331 |  0.886  |                 0.1415 |
| har_seasonal         |     34 |         0.1327 | 0.4145 |  0.4289 |  0.8407 |                 0.0682 |
| har                  |     34 |         0.1357 | 0.4246 |  0.462  |  0.8493 |                 0.0572 |
| persistence          |     34 |         0.1452 | 0.4515 |  0.511  |  0.8946 |                 0      |
| prophet              |     34 |         0.1569 | 0.4668 |  0.4056 |  0.75   |                -0.1262 |
| seasonal_persistence |     34 |         0.1656 | 0.5065 |  0.4583 |  0.8505 |                -0.1771 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags day-level 90% coverage away from 0.90 on 3 consecutive scored days: prophet cov90 0.7500, p 0.0061. The test is two-sided on each model's daily coverage against 0.90 over 34 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063). Bands are left as each model produces them, and the coverage column is the honest record of that.

