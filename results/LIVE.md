# Live scoreboard (generated)

Forecast days scored: 31. Resolved rows: 5880. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     28 |         0.1122 | 0.347  |  0.4717 |  0.8869 |                 0.1868 |
| gbm                  |     31 |         0.1173 | 0.3592 |  0.4005 |  0.8078 |                 0.1556 |
| sarima               |     31 |         0.1229 | 0.3795 |  0.543  |  0.8817 |                 0.1148 |
| har_seasonal         |     31 |         0.1325 | 0.4128 |  0.4355 |  0.8414 |                 0.0456 |
| har                  |     31 |         0.1357 | 0.4238 |  0.4664 |  0.8522 |                 0.0322 |
| persistence          |     31 |         0.1414 | 0.4377 |  0.5242 |  0.9019 |                 0      |
| prophet              |     31 |         0.1629 | 0.4836 |  0.3858 |  0.7339 |                -0.2014 |
| seasonal_persistence |     31 |         0.1644 | 0.501  |  0.4691 |  0.8508 |                -0.2023 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags day-level 90% coverage away from 0.90 on 3 consecutive scored days: prophet cov90 0.7339, p 0.0054. The test is two-sided on each model's daily coverage against 0.90 over 31 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063). Bands are left as each model produces them, and the coverage column is the honest record of that.

