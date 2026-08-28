# Live scoreboard (generated)

Forecast days scored: 25. Resolved rows: 4728. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     22 |         0.117  | 0.3567 |  0.4943 |  0.8807 |                 0.1686 |
| gbm                  |     25 |         0.1244 | 0.3775 |  0.3783 |  0.7833 |                 0.1179 |
| sarima               |     25 |         0.129  | 0.3962 |  0.5383 |  0.8617 |                 0.0868 |
| har_seasonal         |     25 |         0.1376 | 0.4232 |  0.44   |  0.8217 |                 0.0256 |
| har                  |     25 |         0.1393 | 0.4306 |  0.4733 |  0.8383 |                 0.022  |
| persistence          |     25 |         0.1437 | 0.4442 |  0.515  |  0.9017 |                 0      |
| seasonal_persistence |     25 |         0.1711 | 0.5176 |  0.46   |  0.8333 |                -0.2339 |
| prophet              |     25 |         0.176  | 0.5161 |  0.3683 |  0.7    |                -0.2826 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects prophet cov90 0.7000, p 0.0062, day 2 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 25 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

