# Live scoreboard (generated)

Forecast days scored: 47. Resolved rows: 8952. Pending (logged, outcome not yet observed): 192.

Every row here was committed to git before its target hour completed. The commit history is the timestamp evidence.

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     44 |         0.1042 | 0.324  |  0.4915 |  0.8987 |                 0.2249 |      0.1887 |      0.4071 |
| gbm                  |     47 |         0.1112 | 0.3415 |  0.4406 |  0.8324 |                 0.18   |      0.2    |      0.3488 |
| sarima               |     47 |         0.1158 | 0.3569 |  0.5603 |  0.9043 |                 0.1457 |      0.2067 |      0.3267 |
| har_seasonal         |     47 |         0.1258 | 0.3935 |  0.4495 |  0.8626 |                 0.0704 |      0.2637 |      0.141  |
| har                  |     47 |         0.1292 | 0.4051 |  0.4787 |  0.8644 |                 0.0563 |      0.2738 |      0.1084 |
| persistence          |     47 |         0.1382 | 0.4302 |  0.5337 |  0.9096 |                 0      |      0.307  |      0      |
| prophet              |     47 |         0.1413 | 0.424  |  0.4521 |  0.7979 |                -0.0606 |      0.3543 |     -0.1538 |
| seasonal_persistence |     47 |         0.1596 | 0.4899 |  0.4672 |  0.8652 |                -0.1888 |      0.3041 |      0.0098 |

The hourly columns score each of the 24 target hours. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the 24 hourly median forecasts' average against the realized average, over fully resolved days, so lower is better. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, yesterday](fig_live_daily.png)

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The calibration check passes, with no model's day-level 90% coverage separable from 0.90 by more than sampling noise. The test is two-sided on each model's daily coverage against 0.90 over 47 scored days, Bonferroni-corrected across the 8 models tested (per-model alpha 0.0063).

