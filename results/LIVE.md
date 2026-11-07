# Daily record (generated)

Forecast days scored: 95. Resolved rows: 18168. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     92 |         0.1008 | 0.315  |  0.4873 |  0.8863 |                 0.2512 |      0.1662 |      0.3785 |
| gbm                  |     95 |         0.1067 | 0.3311 |  0.4474 |  0.8474 |                 0.2156 |      0.1738 |      0.352  |
| sarima               |     95 |         0.1116 | 0.3452 |  0.5697 |  0.9206 |                 0.1763 |      0.2087 |      0.2218 |
| prophet              |     95 |         0.1187 | 0.3648 |  0.5079 |  0.8557 |                 0.1168 |      0.2432 |      0.093  |
| har_seasonal         |     95 |         0.122  | 0.3865 |  0.4408 |  0.8724 |                 0.1018 |      0.2271 |      0.1532 |
| har                  |     95 |         0.1254 | 0.3972 |  0.4702 |  0.8759 |                 0.0884 |      0.2303 |      0.1413 |
| persistence          |     95 |         0.1388 | 0.4373 |  0.5193 |  0.9136 |                 0      |      0.2682 |      0      |
| seasonal_persistence |     95 |         0.1559 | 0.4829 |  0.4649 |  0.8697 |                -0.1591 |      0.3175 |     -0.1838 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The table above blends the record before and after the model settings changed on 2026-10-23. On the 15 forecast days scored since the change, prophet leads with a mean pinball loss of 0.0965.

Matched on the 92 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.21 to 0.35) and 0.38 on the day-level error (0.22 to 0.54). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

