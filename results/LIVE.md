# Live scoreboard (generated)

Forecast days scored: 21. Resolved rows: 3960. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     18 |         0.1178 | 0.3512 |  0.5116 |  0.8634 |                 0.1982 |
| gbm                  |     21 |         0.1298 | 0.3925 |  0.3849 |  0.7798 |                 0.1202 |
| sarima               |     21 |         0.1367 | 0.4215 |  0.504  |  0.8393 |                 0.0764 |
| har_seasonal         |     21 |         0.1441 | 0.4387 |  0.4345 |  0.7956 |                 0.0276 |
| har                  |     21 |         0.1458 | 0.4457 |  0.4742 |  0.8155 |                 0.0245 |
| persistence          |     21 |         0.1509 | 0.4669 |  0.494  |  0.8829 |                 0      |
| prophet              |     21 |         0.1773 | 0.5143 |  0.3869 |  0.7024 |                -0.2373 |
| seasonal_persistence |     21 |         0.1814 | 0.5446 |  0.4484 |  0.8056 |                -0.2528 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 21 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

