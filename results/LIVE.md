# Live scoreboard (generated)

Forecast days scored: 7. Resolved rows: 1272. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed, so before its outcome was observable; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |         0.1039 | 0.3223 |  0.5521 |  0.8646 |                 0.1965 |
| gbm                  |         0.114  | 0.3471 |  0.3869 |  0.8095 |                 0.1108 |
| sarima               |         0.1306 | 0.3986 |  0.5179 |  0.8512 |                -0.0151 |
| prophet              |         0.1333 | 0.4161 |  0.3869 |  0.8095 |                -0.0706 |
| persistence          |         0.1361 | 0.4386 |  0.4583 |  0.9048 |                 0      |
| har_seasonal         |         0.1401 | 0.4225 |  0.4464 |  0.7798 |                -0.0876 |
| har                  |         0.141  | 0.4281 |  0.4881 |  0.8333 |                -0.0777 |
| seasonal_persistence |         0.1559 | 0.4656 |  0.506  |  0.8452 |                -0.1962 |

The calibration check stays inactive until 10 scored days (7 so far). Coverage columns are provisional; each day contributes ~24 dependent hourly rows, so the effective sample is the day count.

