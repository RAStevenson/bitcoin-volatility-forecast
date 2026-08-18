# Live scoreboard (generated)

Forecast days scored: 15. Resolved rows: 2808. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     12 |         0.0939 | 0.2857 |  0.566  |  0.8958 |                 0.2788 |
| gbm                  |     15 |         0.1155 | 0.3541 |  0.3889 |  0.7861 |                 0.1174 |
| prophet              |     15 |         0.1159 | 0.3594 |  0.4833 |  0.8583 |                 0.0943 |
| sarima               |     15 |         0.1296 | 0.4002 |  0.5306 |  0.8417 |                 0.0182 |
| har_seasonal         |     15 |         0.132  | 0.4077 |  0.4556 |  0.8194 |                -0.0048 |
| persistence          |     15 |         0.1358 | 0.4276 |  0.5139 |  0.9    |                 0      |
| har                  |     15 |         0.1371 | 0.4235 |  0.4778 |  0.8222 |                -0.031  |
| seasonal_persistence |     15 |         0.1785 | 0.5304 |  0.475  |  0.8056 |                -0.3683 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 15 scored days: gbm 0.7861.

