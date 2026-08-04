# Live scoreboard (generated)

Forecast days scored: 1. Resolved rows: 119. Pending (logged, outcome not yet observed): 217.

Every row here was committed to git before its target hour occurred; the commit history is the timestamp evidence.

| model                |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |
|:---------------------|---------------:|-------:|--------:|--------:|-----------------------:|
| sarima               |         0.0691 | 0.2126 |  0.6471 |  1      |                 0.2046 |
| prophet              |         0.0695 | 0.2281 |  0.6471 |  1      |                 0.2202 |
| gbm                  |         0.0825 | 0.2801 |  0.5882 |  0.8824 |                 0.1679 |
| seasonal_persistence |         0.0832 | 0.2464 |  0.7059 |  1      |                -0.0343 |
| har_seasonal         |         0.0878 | 0.2894 |  0.5294 |  0.9412 |                -0.0335 |
| har                  |         0.0931 | 0.3102 |  0.5882 |  1      |                -0.0113 |
| persistence          |         0.0959 | 0.292  |  0.5882 |  1      |                 0      |

