# Live scoreboard (generated)

Forecast days scored: 36. Resolved rows: 6840. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     33 |         0.1081 | 0.3357 |  0.4747 |  0.8952 |                 0.2182 |
| gbm                  |     36 |         0.1153 | 0.3535 |  0.4213 |  0.8102 |                 0.1707 |
| sarima               |     36 |         0.1199 | 0.3711 |  0.5486 |  0.8924 |                 0.1426 |
| har_seasonal         |     36 |         0.1297 | 0.4049 |  0.4421 |  0.8495 |                 0.07   |
| har                  |     36 |         0.1323 | 0.4135 |  0.4769 |  0.8576 |                 0.0617 |
| persistence          |     36 |         0.1422 | 0.4415 |  0.522  |  0.9005 |                 0      |
| prophet              |     36 |         0.1529 | 0.456  |  0.4132 |  0.7627 |                -0.1203 |
| seasonal_persistence |     36 |         0.162  | 0.496  |  0.4618 |  0.8588 |                -0.1771 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects gbm cov90 0.8102, p 0.0062, day 2 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 36 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

