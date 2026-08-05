# Live scoreboard (generated)

Forecast days scored: 2. Resolved rows: 301. Pending (logged, outcome not yet observed): 203.

Every row here was committed to git before its target hour occurred; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| sarima               |         0.0714 | 0.2067 |  0.7292 |  1      |                 0.3024 |
| prophet              |         0.0758 | 0.2386 |  0.625  |  0.9792 |                 0.2818 |
| har_seasonal         |         0.0766 | 0.2282 |  0.625  |  0.9792 |                 0.2394 |
| gbm                  |         0.0785 | 0.2416 |  0.6042 |  0.8542 |                 0.2907 |
| har                  |         0.0807 | 0.2501 |  0.6875 |  0.9792 |                 0.2108 |
| seasonal_persistence |         0.0861 | 0.2446 |  0.7083 |  1      |                 0.1302 |
| persistence          |         0.1074 | 0.3328 |  0.5417 |  0.9792 |                 0      |

