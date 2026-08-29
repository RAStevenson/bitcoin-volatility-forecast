# Live scoreboard (generated)

Forecast days scored: 26. Resolved rows: 4920. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     23 |         0.1179 | 0.3613 |  0.4801 |  0.8786 |                 0.1612 |
| gbm                  |     26 |         0.1237 | 0.3761 |  0.3814 |  0.7821 |                 0.1222 |
| sarima               |     26 |         0.1282 | 0.396  |  0.5321 |  0.8654 |                 0.0913 |
| har_seasonal         |     26 |         0.1382 | 0.4274 |  0.4279 |  0.8221 |                 0.0207 |
| har                  |     26 |         0.1408 | 0.4368 |  0.4615 |  0.8333 |                 0.0122 |
| persistence          |     26 |         0.1437 | 0.4463 |  0.5096 |  0.9022 |                 0      |
| seasonal_persistence |     26 |         0.1695 | 0.5139 |  0.4599 |  0.8365 |                -0.2252 |
| prophet              |     26 |         0.1733 | 0.508  |  0.375  |  0.7083 |                -0.2631 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, flagging no model. It rejects gbm cov90 0.7821, p 0.0043, day 1 of 3, short of the 3 consecutive days it reports on. The test is two-sided on each model's daily coverage against 0.90 over 26 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

