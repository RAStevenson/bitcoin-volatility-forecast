# Live scoreboard (generated)

Forecast days scored: 5. Resolved rows: 888. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |         0.0879 | 0.2648 |  0.6667 |  0.9583 |                 0.3313 |
| prophet              |         0.0999 | 0.3278 |  0.4583 |  0.925  |                 0.1701 |
| gbm                  |         0.1015 | 0.3051 |  0.4583 |  0.8583 |                 0.1887 |
| sarima               |         0.1064 | 0.3181 |  0.625  |  0.925  |                 0.1275 |
| seasonal_persistence |         0.112  | 0.3287 |  0.6333 |  0.9417 |                 0.0827 |
| har_seasonal         |         0.1139 | 0.3432 |  0.525  |  0.9    |                 0.0847 |
| har                  |         0.1212 | 0.368  |  0.5667 |  0.9    |                 0.0443 |
| persistence          |         0.128  | 0.4089 |  0.5    |  0.9333 |                 0      |

The calibration check stays inactive until 10 scored days (5 so far). Coverage columns are provisional; each day contributes ~24 dependent hourly rows, so the effective sample is the day count.

