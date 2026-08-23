# Live scoreboard (generated)

Forecast days scored: 20. Resolved rows: 3768. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     17 |         0.1191 | 0.3545 |  0.5049 |  0.8578 |                 0.1997 |
| gbm                  |     20 |         0.1322 | 0.3994 |  0.3813 |  0.775  |                 0.116  |
| sarima               |     20 |         0.1385 | 0.4246 |  0.5104 |  0.8312 |                 0.0782 |
| har_seasonal         |     20 |         0.1461 | 0.4423 |  0.4396 |  0.7875 |                 0.0278 |
| har                  |     20 |         0.1483 | 0.4515 |  0.4708 |  0.8083 |                 0.0218 |
| persistence          |     20 |         0.1531 | 0.4721 |  0.4896 |  0.8792 |                 0      |
| prophet              |     20 |         0.1753 | 0.5066 |  0.4    |  0.7146 |                -0.2081 |
| seasonal_persistence |     20 |         0.185  | 0.555  |  0.4417 |  0.7958 |                -0.2646 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 20 scored days: gbm 0.7750; har_seasonal 0.7875; prophet 0.7146; seasonal_persistence 0.7958. Bands are left as each model produces them: a 2026-08-21 replay of an adaptive conformal widening rule over the scored days restored coverage on average but could not anticipate a first-day shock such as 2026-08-19, so it was measured and not adopted (see README, Limitations).

