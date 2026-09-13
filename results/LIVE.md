# Live scoreboard (generated)

Forecast days scored: 40. Resolved rows: 7608. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     37 |         0.1071 | 0.3316 |  0.4831 |  0.8896 |                 0.2215 |
| gbm                  |     40 |         0.1142 | 0.3496 |  0.4229 |  0.8188 |                 0.1753 |
| sarima               |     40 |         0.1198 | 0.3711 |  0.5448 |  0.8917 |                 0.1382 |
| har_seasonal         |     40 |         0.1304 | 0.4076 |  0.4385 |  0.849  |                 0.0587 |
| har                  |     40 |         0.1337 | 0.4184 |  0.4635 |  0.8521 |                 0.0458 |
| persistence          |     40 |         0.1415 | 0.4409 |  0.5177 |  0.9031 |                 0      |
| prophet              |     40 |         0.1476 | 0.4406 |  0.4344 |  0.776  |                -0.0845 |
| seasonal_persistence |     40 |         0.1624 | 0.4959 |  0.4667 |  0.8594 |                -0.1812 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 40 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

