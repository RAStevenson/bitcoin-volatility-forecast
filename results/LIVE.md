# Live scoreboard (generated)

Forecast days scored: 9. Resolved rows: 1656. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |      6 |         0.0966 | 0.2985 |  0.5556 |  0.8958 |                 0.2408 |
| gbm                  |      9 |         0.1119 | 0.3428 |  0.3935 |  0.8056 |                 0.1015 |
| sarima               |      9 |         0.1212 | 0.3761 |  0.537  |  0.8796 |                 0.0255 |
| prophet              |      9 |         0.1233 | 0.3878 |  0.412  |  0.8426 |                -0.0047 |
| har_seasonal         |      9 |         0.1286 | 0.3915 |  0.4815 |  0.8241 |                -0.019  |
| persistence          |      9 |         0.1328 | 0.4206 |  0.5    |  0.9028 |                 0      |
| har                  |      9 |         0.1334 | 0.4076 |  0.5046 |  0.8426 |                -0.0453 |
| seasonal_persistence |      9 |         0.1609 | 0.4794 |  0.5046 |  0.8426 |                -0.2688 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check stays inactive until 10 scored days (9 so far). Coverage columns are provisional; each day contributes ~24 dependent hourly rows, so the effective sample is the day count.

