# Live scoreboard (generated)

Forecast days scored: 18. Resolved rows: 3384. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     15 |         0.1179 | 0.3487 |  0.5139 |  0.8444 |                 0.222  |
| gbm                  |     18 |         0.1331 | 0.3981 |  0.3681 |  0.7616 |                 0.1226 |
| sarima               |     18 |         0.1414 | 0.4322 |  0.5093 |  0.8171 |                 0.0712 |
| prophet              |     18 |         0.1465 | 0.4349 |  0.4444 |  0.7801 |                 0.0148 |
| har_seasonal         |     18 |         0.1495 | 0.4518 |  0.4329 |  0.7801 |                 0.0218 |
| har                  |     18 |         0.1532 | 0.4674 |  0.4606 |  0.7917 |                 0.006  |
| persistence          |     18 |         0.1559 | 0.4747 |  0.5093 |  0.8657 |                 0      |
| seasonal_persistence |     18 |         0.1859 | 0.5525 |  0.463  |  0.794  |                -0.2564 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 18 scored days: gbm 0.7616; har 0.7917; har_seasonal 0.7801; prophet 0.7801; seasonal_persistence 0.7940.

