# Live scoreboard (generated)

Forecast days scored: 14. Resolved rows: 2616. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     11 |         0.0968 | 0.2946 |  0.5606 |  0.8864 |                 0.2663 |
| gbm                  |     14 |         0.1178 | 0.3613 |  0.381  |  0.7827 |                 0.1081 |
| prophet              |     14 |         0.1195 | 0.3712 |  0.4643 |  0.8482 |                 0.0753 |
| sarima               |     14 |         0.1335 | 0.413  |  0.5119 |  0.8304 |                -0.001  |
| har_seasonal         |     14 |         0.1344 | 0.4139 |  0.4494 |  0.8095 |                -0.0135 |
| persistence          |     14 |         0.1378 | 0.4312 |  0.5119 |  0.8929 |                 0      |
| har                  |     14 |         0.1387 | 0.4274 |  0.4643 |  0.8214 |                -0.0317 |
| seasonal_persistence |     14 |         0.1737 | 0.5177 |  0.4821 |  0.8125 |                -0.3173 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 14 scored days: gbm 0.7827.

