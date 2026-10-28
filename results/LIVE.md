# Daily record (generated)

Forecast days scored: 85. Resolved rows: 16248. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     82 |         0.0991 | 0.31   |  0.4985 |  0.8968 |                 0.2526 |      0.1549 |      0.3983 |
| gbm                  |     85 |         0.1055 | 0.3278 |  0.4529 |  0.85   |                 0.2115 |      0.1651 |      0.3618 |
| sarima               |     85 |         0.1099 | 0.3387 |  0.5804 |  0.9216 |                 0.1748 |      0.1981 |      0.234  |
| har_seasonal         |     85 |         0.121  | 0.3828 |  0.4466 |  0.875  |                 0.0921 |      0.2196 |      0.1508 |
| prophet              |     85 |         0.1211 | 0.3714 |  0.5    |  0.85   |                 0.0849 |      0.2485 |      0.039  |
| har                  |     85 |         0.124  | 0.392  |  0.475  |  0.8794 |                 0.0815 |      0.2228 |      0.1383 |
| persistence          |     85 |         0.1362 | 0.4275 |  0.5294 |  0.9167 |                 0      |      0.2586 |      0      |
| seasonal_persistence |     85 |         0.154  | 0.4751 |  0.4779 |  0.8716 |                -0.1618 |      0.3106 |     -0.2011 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 5 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0925.

Matched on the 82 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.20 to 0.35) and 0.40 on the day-level error (0.22 to 0.58). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

