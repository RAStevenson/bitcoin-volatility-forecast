# Live scoreboard (generated)

Forecast days scored: 3. Resolved rows: 504. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour occurred; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| sarima               |         0.0727 | 0.2208 |  0.6944 |  1      |                 0.2972 |
| prophet              |         0.0777 | 0.2547 |  0.5417 |  0.9861 |                 0.2602 |
| gbm                  |         0.0795 | 0.2497 |  0.5278 |  0.8889 |                 0.2503 |
| har_seasonal         |         0.0795 | 0.2412 |  0.625  |  0.9722 |                 0.2232 |
| har                  |         0.0865 | 0.27   |  0.6667 |  0.9583 |                 0.162  |
| seasonal_persistence |         0.0882 | 0.2546 |  0.7083 |  1      |                 0.1325 |
| persistence          |         0.1061 | 0.3339 |  0.5556 |  0.9861 |                 0      |

