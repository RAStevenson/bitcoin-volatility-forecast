# Daily record (generated)

Forecast days scored: 103. Resolved rows: 19704. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |    100 |         0.1044 | 0.325  |  0.4825 |  0.8812 |                 0.2467 |      0.1818 |      0.3515 |
| gbm                  |    103 |         0.1083 | 0.3356 |  0.4458 |  0.8422 |                 0.2254 |      0.1821 |      0.3514 |
| sarima               |    103 |         0.1154 | 0.3566 |  0.5603 |  0.9114 |                 0.1724 |      0.2236 |      0.2035 |
| prophet              |    103 |         0.1243 | 0.3786 |  0.4996 |  0.8463 |                 0.1013 |      0.2587 |      0.0784 |
| har_seasonal         |    103 |         0.125  | 0.3952 |  0.4377 |  0.8637 |                 0.1052 |      0.2429 |      0.1347 |
| har                  |    103 |         0.128  | 0.4054 |  0.464  |  0.8693 |                 0.095  |      0.2467 |      0.1211 |
| persistence          |    103 |         0.1427 | 0.4469 |  0.5178 |  0.9029 |                 0      |      0.2807 |      0      |
| seasonal_persistence |    103 |         0.1585 | 0.489  |  0.462  |  0.8637 |                -0.1478 |      0.3262 |     -0.162  |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 23 forecast days scored since the change, gbm leads with a mean pinball loss of 0.1161.

Matched on the 100 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.27 on the hourly pinball loss (95% interval 0.21 to 0.34) and 0.35 on the day-level error (0.20 to 0.50). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

