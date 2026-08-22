# Live scoreboard (generated)

Forecast days scored: 19. Resolved rows: 3576. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |     16 |         0.1194 | 0.3539 |  0.5104 |  0.8516 |                 0.198  |
| gbm                  |     19 |         0.1309 | 0.391  |  0.3969 |  0.7719 |                 0.125  |
| sarima               |     19 |         0.1395 | 0.4266 |  0.5132 |  0.8246 |                 0.0708 |
| har_seasonal         |     19 |         0.147  | 0.4446 |  0.4408 |  0.7895 |                 0.0234 |
| har                  |     19 |         0.1506 | 0.4582 |  0.4737 |  0.8004 |                 0.0085 |
| persistence          |     19 |         0.1534 | 0.4692 |  0.5044 |  0.8728 |                 0      |
| prophet              |     19 |         0.1669 | 0.4831 |  0.4211 |  0.7412 |                -0.1432 |
| seasonal_persistence |     19 |         0.1837 | 0.5473 |  0.4605 |  0.7982 |                -0.2552 |

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check flags cov90 outside [0.80, 0.98] over 19 scored days: gbm 0.7719; har_seasonal 0.7895; prophet 0.7412; seasonal_persistence 0.7982. Bands are left as each model produces them: a 2026-08-21 replay of an adaptive conformal widening rule over the scored days restored coverage on average but could not anticipate a first-day shock such as 2026-08-19, so it was measured and not adopted (see README, Limitations).

