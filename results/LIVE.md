# Live scoreboard (generated)

Forecast days scored: 4. Resolved rows: 696. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour occurred; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| nhits                |         0.0625 | 0.1842 |  0.7917 |  1      |                 0.4224 |
| sarima               |         0.0715 | 0.2182 |  0.7188 |  1      |                 0.3124 |
| gbm                  |         0.0784 | 0.2484 |  0.5    |  0.9167 |                 0.2689 |
| har_seasonal         |         0.0811 | 0.2504 |  0.6042 |  0.9792 |                 0.2378 |
| prophet              |         0.0818 | 0.2744 |  0.5    |  0.9896 |                 0.2082 |
| har                  |         0.0857 | 0.2708 |  0.6458 |  0.9688 |                 0.2081 |
| seasonal_persistence |         0.0869 | 0.248  |  0.7083 |  1      |                 0.1533 |
| persistence          |         0.1108 | 0.349  |  0.5521 |  0.9792 |                 0      |

The calibration check stays inactive until 10 scored days (4 so far). Coverage columns are provisional; each day contributes ~24 dependent hourly rows, so the effective sample is the day count.

