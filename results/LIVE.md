# Live scoreboard (generated)

Forecast days scored: 8. Resolved rows: 1464. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |         0.1027 | 0.3203 |  0.5333 |  0.875  |                 0.2153 |
| gbm                  |         0.117  | 0.3573 |  0.3646 |  0.7865 |                 0.0824 |
| sarima               |         0.1274 | 0.3935 |  0.5104 |  0.8646 |                 0.0062 |
| prophet              |         0.1297 | 0.4062 |  0.3958 |  0.8229 |                -0.0329 |
| har_seasonal         |         0.1351 | 0.4123 |  0.4427 |  0.8021 |                -0.0464 |
| persistence          |         0.1365 | 0.4368 |  0.4792 |  0.8958 |                 0      |
| har                  |         0.139  | 0.4259 |  0.4792 |  0.8281 |                -0.0629 |
| seasonal_persistence |         0.1696 | 0.5062 |  0.4792 |  0.8229 |                -0.2976 |

The calibration check stays inactive until 10 scored days (8 so far). Coverage columns are provisional; each day contributes ~24 dependent hourly rows, so the effective sample is the day count.

