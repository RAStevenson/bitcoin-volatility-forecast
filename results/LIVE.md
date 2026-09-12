# Live scoreboard (generated)

Forecast days scored: 39. Resolved rows: 7416. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     36 |         0.107  | 0.3313 |  0.4826 |  0.8935 |                 0.2258 |
| gbm                  |     39 |         0.1148 | 0.3513 |  0.4199 |  0.8162 |                 0.1753 |
| sarima               |     39 |         0.1194 | 0.3695 |  0.5502 |  0.8932 |                 0.1435 |
| har_seasonal         |     39 |         0.1293 | 0.404  |  0.4455 |  0.8526 |                 0.0715 |
| har                  |     39 |         0.1328 | 0.4155 |  0.469  |  0.8547 |                 0.0573 |
| persistence          |     39 |         0.1422 | 0.4427 |  0.516  |  0.9017 |                 0      |
| prophet              |     39 |         0.1489 | 0.4439 |  0.4306 |  0.7735 |                -0.0902 |
| seasonal_persistence |     39 |         0.1589 | 0.487  |  0.469  |  0.8654 |                -0.1531 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 39 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

