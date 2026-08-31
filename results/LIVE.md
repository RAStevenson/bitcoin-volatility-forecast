# Live scoreboard (generated)

Forecast days scored: 28. Resolved rows: 5304. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     25 |         0.1176 | 0.3618 |  0.47   |  0.8767 |                 0.1779 |
| gbm                  |     28 |         0.1211 | 0.369  |  0.3899 |  0.7932 |                 0.157  |
| sarima               |     28 |         0.1279 | 0.3975 |  0.5223 |  0.869  |                 0.112  |
| har_seasonal         |     28 |         0.1377 | 0.4289 |  0.4167 |  0.8244 |                 0.0417 |
| har                  |     28 |         0.1403 | 0.4376 |  0.4509 |  0.8393 |                 0.0331 |
| persistence          |     28 |         0.1463 | 0.4554 |  0.5045 |  0.8943 |                 0      |
| prophet              |     28 |         0.1686 | 0.4969 |  0.3795 |  0.7202 |                -0.2041 |
| seasonal_persistence |     28 |         0.1704 | 0.5183 |  0.4554 |  0.8363 |                -0.2056 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags day-level 90% coverage away from 0.90 on 3 consecutive scored days: gbm cov90 0.7932, p 0.0058. The test is two-sided on each model's daily coverage against 0.90 over 28 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063). Bands are left as each model produces them, and the coverage column is the honest record of that.

