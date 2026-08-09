# Live scoreboard (generated)

Forecast days scored: 6. Resolved rows: 1080. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |         0.095  | 0.2956 |  0.5833 |  0.9028 |                 0.2271 |
| gbm                  |         0.1099 | 0.3314 |  0.4097 |  0.8194 |                 0.0893 |
| prophet              |         0.121  | 0.3866 |  0.4028 |  0.8403 |                -0.0294 |
| persistence          |         0.1272 | 0.4068 |  0.5    |  0.9306 |                 0      |
| sarima               |         0.1274 | 0.3895 |  0.5347 |  0.8611 |                -0.0708 |
| har_seasonal         |         0.1366 | 0.4083 |  0.4653 |  0.8056 |                -0.143  |
| seasonal_persistence |         0.1396 | 0.413  |  0.5556 |  0.8889 |                -0.1521 |
| har                  |         0.1419 | 0.4273 |  0.4931 |  0.8333 |                -0.1697 |

The calibration check stays inactive until 10 scored days (6 so far). Coverage columns are provisional; each day contributes ~24 dependent hourly rows, so the effective sample is the day count.

