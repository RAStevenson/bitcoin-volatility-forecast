# Live scoreboard (generated)

Forecast days scored: 11. Resolved rows: 2040. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |      8 |         0.0889 | 0.2717 |  0.5781 |  0.9115 |                 0.2646 |
| gbm                  |     11 |         0.1079 | 0.3319 |  0.3977 |  0.8144 |                 0.1002 |
| sarima               |     11 |         0.1129 | 0.3483 |  0.5833 |  0.8939 |                 0.0471 |
| prophet              |     11 |         0.114  | 0.3574 |  0.4621 |  0.8636 |                 0.0283 |
| har_seasonal         |     11 |         0.1212 | 0.3713 |  0.5114 |  0.8485 |                -0.0026 |
| persistence          |     11 |         0.1264 | 0.3939 |  0.5379 |  0.9129 |                 0      |
| har                  |     11 |         0.127  | 0.3888 |  0.5265 |  0.8636 |                -0.0352 |
| seasonal_persistence |     11 |         0.1494 | 0.4444 |  0.5455 |  0.8674 |                -0.2385 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with all models inside the cov90 band [0.80, 0.98] over 11 scored days.

