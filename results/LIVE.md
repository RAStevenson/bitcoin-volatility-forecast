# Live scoreboard (generated)

Forecast days scored: 12. Resolved rows: 2232. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |      9 |         0.0859 | 0.26   |  0.6065 |  0.9213 |                 0.2962 |
| gbm                  |     12 |         0.1086 | 0.3354 |  0.3993 |  0.816  |                 0.1082 |
| prophet              |     12 |         0.11   | 0.3437 |  0.4896 |  0.875  |                 0.0739 |
| sarima               |     12 |         0.1166 | 0.3621 |  0.566  |  0.8854 |                 0.0356 |
| har_seasonal         |     12 |         0.1206 | 0.3732 |  0.4965 |  0.8542 |                 0.0174 |
| har                  |     12 |         0.1274 | 0.3935 |  0.5069 |  0.8646 |                -0.0207 |
| persistence          |     12 |         0.1279 | 0.4023 |  0.5208 |  0.9167 |                 0      |
| seasonal_persistence |     12 |         0.149  | 0.4445 |  0.5382 |  0.8681 |                -0.2201 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with all models inside the cov90 band [0.80, 0.98] over 12 scored days.

