# Live scoreboard (generated)

Forecast days scored: 30. Resolved rows: 5688. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     27 |         0.1134 | 0.3502 |  0.4738 |  0.8827 |                 0.186  |
| gbm                  |     30 |         0.118  | 0.3606 |  0.3986 |  0.8028 |                 0.158  |
| sarima               |     30 |         0.1241 | 0.3832 |  0.5417 |  0.8778 |                 0.1155 |
| har_seasonal         |     30 |         0.1338 | 0.4166 |  0.4319 |  0.8361 |                 0.0447 |
| har                  |     30 |         0.1367 | 0.4264 |  0.4653 |  0.8486 |                 0.0344 |
| persistence          |     30 |         0.1428 | 0.442  |  0.5222 |  0.8986 |                 0      |
| prophet              |     30 |         0.1642 | 0.4863 |  0.3875 |  0.7306 |                -0.2001 |
| seasonal_persistence |     30 |         0.166  | 0.5051 |  0.4681 |  0.8458 |                -0.2029 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects prophet cov90 0.7306, p 0.0060, day 2 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 30 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

