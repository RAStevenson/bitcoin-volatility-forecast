# Daily record (generated)

Forecast days scored: 86. Resolved rows: 16440. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     83 |         0.0991 | 0.3102 |  0.4985 |  0.8971 |                 0.2535 |      0.156  |      0.3981 |
| gbm                  |     86 |         0.1052 | 0.3269 |  0.454  |  0.8508 |                 0.2149 |      0.1635 |      0.3717 |
| sarima               |     86 |         0.1098 | 0.3382 |  0.5814 |  0.922  |                 0.1767 |      0.1973 |      0.2418 |
| prophet              |     86 |         0.1206 | 0.3701 |  0.5015 |  0.8508 |                 0.0896 |      0.2462 |      0.0541 |
| har_seasonal         |     86 |         0.1207 | 0.382  |  0.4482 |  0.8755 |                 0.0957 |      0.2195 |      0.1566 |
| har                  |     86 |         0.1238 | 0.3914 |  0.4763 |  0.8803 |                 0.0842 |      0.2228 |      0.1441 |
| persistence          |     86 |         0.1363 | 0.4283 |  0.5291 |  0.9167 |                 0      |      0.2603 |      0      |
| seasonal_persistence |     86 |         0.1536 | 0.4739 |  0.4782 |  0.8726 |                -0.1573 |      0.3083 |     -0.1844 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 6 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0909.

Matched on the 83 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.20 to 0.35) and 0.40 on the day-level error (0.22 to 0.57). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

