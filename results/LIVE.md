# Live scoreboard (generated)

Forecast days scored: 37. Resolved rows: 6984. Pending (logged, outcome not yet observed): 240.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     34 |         0.107  | 0.3322 |  0.4804 |  0.8963 |                 0.2246 |
| gbm                  |     37 |         0.1144 | 0.3504 |  0.419  |  0.8126 |                 0.1755 |
| sarima               |     37 |         0.1192 | 0.3687 |  0.5511 |  0.8944 |                 0.1454 |
| har_seasonal         |     37 |         0.1293 | 0.4042 |  0.4436 |  0.8503 |                 0.0688 |
| har                  |     37 |         0.132  | 0.4125 |  0.4742 |  0.857  |                 0.0605 |
| persistence          |     37 |         0.1418 | 0.4411 |  0.5181 |  0.9027 |                 0      |
| prophet              |     37 |         0.1512 | 0.4509 |  0.4203 |  0.7676 |                -0.1097 |
| seasonal_persistence |     37 |         0.1604 | 0.4908 |  0.4682 |  0.8618 |                -0.1672 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 37 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

