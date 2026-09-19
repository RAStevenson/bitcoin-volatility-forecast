# Live scoreboard (generated)

Forecast days scored: 46. Resolved rows: 8760. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     43 |         0.1047 | 0.3254 |  0.4884 |  0.8983 |                 0.2269 |      0.191  |      0.4046 |
| gbm                  |     46 |         0.1117 | 0.3432 |  0.4384 |  0.8315 |                 0.1817 |      0.1997 |      0.354  |
| sarima               |     46 |         0.1161 | 0.3577 |  0.5607 |  0.9022 |                 0.1485 |      0.2088 |      0.3245 |
| har_seasonal         |     46 |         0.1258 | 0.3931 |  0.4556 |  0.8623 |                 0.0774 |      0.2645 |      0.1444 |
| har                  |     46 |         0.1297 | 0.4062 |  0.481  |  0.8641 |                 0.0601 |      0.2756 |      0.1083 |
| persistence          |     46 |         0.1392 | 0.4338 |  0.5272 |  0.9076 |                 0      |      0.3091 |      0      |
| prophet              |     46 |         0.1415 | 0.4246 |  0.452  |  0.7971 |                -0.055  |      0.3525 |     -0.1404 |
| seasonal_persistence |     46 |         0.159  | 0.4876 |  0.471  |  0.865  |                -0.1768 |      0.3018 |      0.0235 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, yesterday](fig_live_daily.png)

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 46 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

