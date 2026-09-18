# Live scoreboard (generated)

Forecast days scored: 45. Resolved rows: 8568. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     42 |         0.1046 | 0.3247 |  0.4881 |  0.8968 |                 0.2271 |      0.1874 |      0.4136 |
| gbm                  |     45 |         0.1113 | 0.3424 |  0.437  |  0.8306 |                 0.1834 |      0.194  |      0.3693 |
| sarima               |     45 |         0.1167 | 0.3593 |  0.5611 |  0.9009 |                 0.1456 |      0.2096 |      0.3186 |
| har_seasonal         |     45 |         0.1265 | 0.3947 |  0.4546 |  0.8611 |                 0.0723 |      0.2663 |      0.1344 |
| har                  |     45 |         0.1299 | 0.4062 |  0.4815 |  0.863  |                 0.0583 |      0.2767 |      0.1006 |
| persistence          |     45 |         0.1392 | 0.4335 |  0.5278 |  0.9074 |                 0      |      0.3076 |      0      |
| prophet              |     45 |         0.142  | 0.4254 |  0.4528 |  0.7954 |                -0.0593 |      0.3504 |     -0.139  |
| seasonal_persistence |     45 |         0.1597 | 0.4884 |  0.475  |  0.863  |                -0.1821 |      0.3064 |      0.004  |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, yesterday](fig_live_daily.png)

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 45 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

