# Live scoreboard (generated)

Forecast days scored: 24. Resolved rows: 4536. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     21 |         0.1179 | 0.3578 |  0.5099 |  0.881  |                 0.1622 |
| gbm                  |     24 |         0.1263 | 0.3813 |  0.3681 |  0.7743 |                 0.1045 |
| sarima               |     24 |         0.1311 | 0.4034 |  0.5295 |  0.8576 |                 0.072  |
| har_seasonal         |     24 |         0.139  | 0.4264 |  0.441  |  0.816  |                 0.0164 |
| har                  |     24 |         0.1407 | 0.4333 |  0.4792 |  0.8316 |                 0.0138 |
| persistence          |     24 |         0.1442 | 0.4443 |  0.5208 |  0.8976 |                 0      |
| seasonal_persistence |     24 |         0.1738 | 0.5255 |  0.4531 |  0.8264 |                -0.2522 |
| prophet              |     24 |         0.1792 | 0.5237 |  0.3628 |  0.691  |                -0.3059 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects gbm cov90 0.7743, p 0.0043, day 2 of 3; prophet cov90 0.6910, p 0.0059, day 1 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 24 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

