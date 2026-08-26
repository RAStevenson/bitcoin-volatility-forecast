# Live scoreboard (generated)

Forecast days scored: 23. Resolved rows: 4344. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     20 |         0.1198 | 0.3631 |  0.5042 |  0.875  |                 0.1598 |
| gbm                  |     23 |         0.1281 | 0.3873 |  0.3732 |  0.7736 |                 0.1033 |
| sarima               |     23 |         0.1332 | 0.4116 |  0.5181 |  0.8514 |                 0.0683 |
| har_seasonal         |     23 |         0.141  | 0.4312 |  0.4384 |  0.808  |                 0.0156 |
| har                  |     23 |         0.1427 | 0.4383 |  0.4783 |  0.8243 |                 0.0131 |
| persistence          |     23 |         0.1459 | 0.4502 |  0.5127 |  0.8931 |                 0      |
| seasonal_persistence |     23 |         0.1772 | 0.5356 |  0.4493 |  0.8188 |                -0.262  |
| prophet              |     23 |         0.1814 | 0.5291 |  0.3623 |  0.6848 |                -0.3075 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects gbm cov90 0.7736, p 0.0058, day 1 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 23 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

