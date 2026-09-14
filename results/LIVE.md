# Live scoreboard (generated)

Forecast days scored: 41. Resolved rows: 7800. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     38 |         0.1069 | 0.3314 |  0.4825 |  0.8914 |                 0.227  |
| gbm                  |     41 |         0.1137 | 0.3488 |  0.4258 |  0.8211 |                 0.1822 |
| sarima               |     41 |         0.1196 | 0.3718 |  0.5407 |  0.8943 |                 0.1445 |
| har_seasonal         |     41 |         0.13   | 0.4066 |  0.437  |  0.8506 |                 0.0656 |
| har                  |     41 |         0.1327 | 0.4155 |  0.4665 |  0.8557 |                 0.0575 |
| persistence          |     41 |         0.1422 | 0.4438 |  0.5132 |  0.9004 |                 0      |
| prophet              |     41 |         0.1464 | 0.4386 |  0.4339 |  0.7805 |                -0.0712 |
| seasonal_persistence |     41 |         0.1635 | 0.5006 |  0.4604 |  0.8577 |                -0.184  |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 41 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

