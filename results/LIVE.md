# Live scoreboard (generated)

Forecast days scored: 35. Resolved rows: 6648. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     32 |         0.1094 | 0.3397 |  0.4727 |  0.8932 |                 0.2182 |
| gbm                  |     35 |         0.1167 | 0.3579 |  0.4131 |  0.806  |                 0.1711 |
| sarima               |     35 |         0.1213 | 0.3764 |  0.5381 |  0.8893 |                 0.143  |
| har_seasonal         |     35 |         0.1313 | 0.4106 |  0.4321 |  0.8452 |                 0.0692 |
| har                  |     35 |         0.1339 | 0.4188 |  0.469  |  0.8536 |                 0.0617 |
| persistence          |     35 |         0.144  | 0.4481 |  0.5107 |  0.8976 |                 0      |
| prophet              |     35 |         0.1552 | 0.4628 |  0.406  |  0.756  |                -0.1236 |
| seasonal_persistence |     35 |         0.1635 | 0.4998 |  0.4643 |  0.8548 |                -0.1728 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects gbm cov90 0.8060, p 0.0051, day 1 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 35 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

