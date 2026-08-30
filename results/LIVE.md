# Live scoreboard (generated)

Forecast days scored: 27. Resolved rows: 5112. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     24 |         0.1169 | 0.3582 |  0.4774 |  0.8785 |                 0.1552 |
| gbm                  |     27 |         0.1216 | 0.3691 |  0.3904 |  0.787  |                 0.1259 |
| sarima               |     27 |         0.1271 | 0.394  |  0.5309 |  0.8688 |                 0.0864 |
| har_seasonal         |     27 |         0.1383 | 0.4295 |  0.4182 |  0.821  |                 0.0048 |
| har                  |     27 |         0.1409 | 0.4382 |  0.4522 |  0.8364 |                -0.004  |
| persistence          |     27 |         0.1415 | 0.4385 |  0.5201 |  0.9059 |                 0      |
| seasonal_persistence |     27 |         0.1686 | 0.5112 |  0.463  |  0.838  |                -0.2341 |
| prophet              |     27 |         0.1696 | 0.4986 |  0.3812 |  0.7191 |                -0.2516 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects gbm cov90 0.7870, p 0.0047, day 2 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 27 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

