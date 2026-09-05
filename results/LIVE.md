# Live scoreboard (generated)

Forecast days scored: 32. Resolved rows: 6072. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     29 |         0.1121 | 0.3466 |  0.4684 |  0.8851 |                 0.1997 |
| gbm                  |     32 |         0.119  | 0.3642 |  0.3984 |  0.7982 |                 0.1561 |
| sarima               |     32 |         0.1243 | 0.3854 |  0.5326 |  0.8815 |                 0.1194 |
| har_seasonal         |     32 |         0.1351 | 0.4215 |  0.4245 |  0.8333 |                 0.0409 |
| har                  |     32 |         0.1385 | 0.4324 |  0.4557 |  0.8411 |                 0.0273 |
| persistence          |     32 |         0.1436 | 0.4458 |  0.5169 |  0.8997 |                 0      |
| prophet              |     32 |         0.1612 | 0.4775 |  0.3971 |  0.7383 |                -0.1695 |
| seasonal_persistence |     32 |         0.1658 | 0.5069 |  0.4583 |  0.849  |                -0.1943 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags day-level 90% coverage away from 0.90 on 3 consecutive scored days: prophet cov90 0.7383, p 0.0052. The test is two-sided on each model's daily coverage against 0.90 over 32 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063). Bands are left as each model produces them, and the coverage column is the honest record of that.

