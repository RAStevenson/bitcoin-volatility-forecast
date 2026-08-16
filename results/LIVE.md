# Live scoreboard (generated)

Forecast days scored: 13. Resolved rows: 2424. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     10 |         0.0925 | 0.2791 |  0.575  |  0.9042 |                 0.2367 |
| gbm                  |     13 |         0.1128 | 0.3421 |  0.3878 |  0.7853 |                 0.0648 |
| prophet              |     13 |         0.116  | 0.3615 |  0.4744 |  0.8558 |                 0.0199 |
| persistence          |     13 |         0.1264 | 0.3963 |  0.5353 |  0.9199 |                 0      |
| sarima               |     13 |         0.1314 | 0.4049 |  0.5256 |  0.8397 |                -0.0903 |
| har_seasonal         |     13 |         0.132  | 0.4048 |  0.4679 |  0.8173 |                -0.0907 |
| har                  |     13 |         0.1379 | 0.4224 |  0.4744 |  0.8333 |                -0.1213 |
| seasonal_persistence |     13 |         0.1595 | 0.4762 |  0.516  |  0.8397 |                -0.3164 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 13 scored days: gbm 0.7853.

