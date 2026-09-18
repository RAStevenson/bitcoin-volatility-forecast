# Live scoreboard (generated)

Forecast days scored: 45. Resolved rows: 8568. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     42 |         0.1046 | 0.3247 |  0.4881 |  0.8968 |                 0.2271 |
| gbm                  |     45 |         0.1113 | 0.3424 |  0.437  |  0.8306 |                 0.1834 |
| sarima               |     45 |         0.1167 | 0.3593 |  0.5611 |  0.9009 |                 0.1456 |
| har_seasonal         |     45 |         0.1265 | 0.3947 |  0.4546 |  0.8611 |                 0.0723 |
| har                  |     45 |         0.1299 | 0.4062 |  0.4815 |  0.863  |                 0.0583 |
| persistence          |     45 |         0.1392 | 0.4335 |  0.5278 |  0.9074 |                 0      |
| prophet              |     45 |         0.142  | 0.4254 |  0.4528 |  0.7954 |                -0.0593 |
| seasonal_persistence |     45 |         0.1597 | 0.4884 |  0.475  |  0.863  |                -0.1821 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 45 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

