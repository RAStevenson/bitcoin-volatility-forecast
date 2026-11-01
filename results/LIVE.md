# Daily record (generated)

Forecast days scored: 89. Resolved rows: 17016. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     86 |         0.0997 | 0.312  |  0.4966 |  0.8953 |                 0.2561 |      0.16   |      0.3946 |
| gbm                  |     89 |         0.1062 | 0.3287 |  0.4508 |  0.8478 |                 0.2156 |      0.1694 |      0.3614 |
| sarima               |     89 |         0.111  | 0.3427 |  0.5758 |  0.9209 |                 0.1766 |      0.2069 |      0.2198 |
| prophet              |     89 |         0.1203 | 0.3692 |  0.5023 |  0.8511 |                 0.1009 |      0.248  |      0.065  |
| har_seasonal         |     89 |         0.1219 | 0.3855 |  0.4434 |  0.8727 |                 0.097  |      0.2268 |      0.1449 |
| har                  |     89 |         0.125  | 0.3958 |  0.471  |  0.8773 |                 0.0845 |      0.2298 |      0.1334 |
| persistence          |     89 |         0.1378 | 0.4329 |  0.5253 |  0.9143 |                 0      |      0.2652 |      0      |
| seasonal_persistence |     89 |         0.156  | 0.4819 |  0.4691 |  0.8694 |                -0.1647 |      0.3191 |     -0.2033 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 9 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0973.

Matched on the 86 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.39 on the day-level error (0.23 to 0.56). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

