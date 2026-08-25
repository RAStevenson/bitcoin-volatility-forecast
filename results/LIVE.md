# Live scoreboard (generated)

Forecast days scored: 22. Resolved rows: 4152. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     19 |         0.1218 | 0.3692 |  0.4934 |  0.8684 |                 0.1615 |
| gbm                  |     22 |         0.1295 | 0.3911 |  0.3788 |  0.7746 |                 0.1117 |
| sarima               |     22 |         0.136  | 0.4213 |  0.5038 |  0.8447 |                 0.0671 |
| har_seasonal         |     22 |         0.1435 | 0.4384 |  0.4318 |  0.8011 |                 0.0187 |
| har                  |     22 |         0.1453 | 0.4458 |  0.4735 |  0.8163 |                 0.0145 |
| persistence          |     22 |         0.1489 | 0.461  |  0.4981 |  0.8883 |                 0      |
| seasonal_persistence |     22 |         0.1795 | 0.5416 |  0.4451 |  0.8125 |                -0.2564 |
| prophet              |     22 |         0.1825 | 0.5296 |  0.3712 |  0.6818 |                -0.2895 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 22 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

