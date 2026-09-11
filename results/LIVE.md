# Live scoreboard (generated)

Forecast days scored: 38. Resolved rows: 7224. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     35 |         0.1058 | 0.3285 |  0.4845 |  0.8988 |                 0.2246 |
| gbm                  |     38 |         0.1131 | 0.3468 |  0.4254 |  0.818  |                 0.1754 |
| sarima               |     38 |         0.1176 | 0.363  |  0.5592 |  0.8969 |                 0.1462 |
| har_seasonal         |     38 |         0.1277 | 0.3992 |  0.4518 |  0.8553 |                 0.0701 |
| har                  |     38 |         0.1305 | 0.4082 |  0.4759 |  0.8607 |                 0.0607 |
| persistence          |     38 |         0.1402 | 0.4359 |  0.5241 |  0.9057 |                 0      |
| prophet              |     38 |         0.149  | 0.4446 |  0.4298 |  0.773  |                -0.106  |
| seasonal_persistence |     38 |         0.1587 | 0.4847 |  0.4759 |  0.864  |                -0.1668 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 38 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

