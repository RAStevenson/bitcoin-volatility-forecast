# Live scoreboard (generated)

Forecast days scored: 29. Resolved rows: 5496. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     26 |         0.1155 | 0.3564 |  0.4696 |  0.8782 |                 0.1828 |
| gbm                  |     29 |         0.1196 | 0.3653 |  0.3922 |  0.7974 |                 0.1573 |
| sarima               |     29 |         0.126  | 0.3901 |  0.5302 |  0.8736 |                 0.1149 |
| har_seasonal         |     29 |         0.1359 | 0.4233 |  0.4239 |  0.8305 |                 0.0425 |
| har                  |     29 |         0.1385 | 0.4319 |  0.4555 |  0.8448 |                 0.0345 |
| persistence          |     29 |         0.1449 | 0.4499 |  0.5129 |  0.8951 |                 0      |
| prophet              |     29 |         0.1661 | 0.4903 |  0.3894 |  0.7241 |                -0.1985 |
| seasonal_persistence |     29 |         0.1689 | 0.5141 |  0.4598 |  0.8405 |                -0.2078 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects prophet cov90 0.7241, p 0.0057, day 1 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 29 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

