# Live scoreboard (generated)

Forecast days scored: 16. Resolved rows: 3000. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     13 |         0.093  | 0.2844 |  0.5577 |  0.8942 |                 0.2711 |
| prophet              |     16 |         0.1135 | 0.3529 |  0.4974 |  0.8646 |                 0.0963 |
| gbm                  |     16 |         0.1136 | 0.3491 |  0.3776 |  0.7891 |                 0.1156 |
| sarima               |     16 |         0.1268 | 0.3921 |  0.5391 |  0.8516 |                 0.0173 |
| har_seasonal         |     16 |         0.1292 | 0.3986 |  0.4609 |  0.8281 |                -0.0022 |
| persistence          |     16 |         0.1335 | 0.4168 |  0.5339 |  0.9036 |                 0      |
| har                  |     16 |         0.1342 | 0.4139 |  0.4922 |  0.8307 |                -0.027  |
| seasonal_persistence |     16 |         0.1734 | 0.515  |  0.4896 |  0.8151 |                -0.3581 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 16 scored days: gbm 0.7891.

