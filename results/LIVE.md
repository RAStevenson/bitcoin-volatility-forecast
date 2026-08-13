# Live scoreboard (generated)

Forecast days scored: 10. Resolved rows: 1848. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |      7 |         0.0915 | 0.2814 |  0.5774 |  0.9048 |                 0.2613 |
| gbm                  |     10 |         0.1084 | 0.3318 |  0.4083 |  0.8083 |                 0.1121 |
| sarima               |     10 |         0.117  | 0.3625 |  0.5667 |  0.8875 |                 0.0354 |
| prophet              |     10 |         0.1186 | 0.3728 |  0.4417 |  0.8542 |                 0.01   |
| har_seasonal         |     10 |         0.1239 | 0.377  |  0.5    |  0.8375 |                -0.005  |
| har                  |     10 |         0.1291 | 0.3933 |  0.5208 |  0.8542 |                -0.0331 |
| persistence          |     10 |         0.1293 | 0.4055 |  0.525  |  0.9083 |                 0      |
| seasonal_persistence |     10 |         0.1541 | 0.458  |  0.5375 |  0.8542 |                -0.2482 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with all models inside the cov90 band [0.80, 0.98] over 10 scored days.

