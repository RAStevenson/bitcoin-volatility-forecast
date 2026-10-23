# Daily record (generated)

Forecast days scored: 80. Resolved rows: 15288. Pending (logged, outcome not yet observed): 192.

Every forecast-log row from an earlier run was committed to git before its target hour completed, except on the 5 days listed in [TIMING.md](TIMING.md).

| model                |   days |   pinball_mean |    mae |   cov50 |   cov90 |   skill_vs_persistence |   day_error |   day_skill |
|:---------------------|-------:|---------------:|-------:|--------:|--------:|-----------------------:|------------:|------------:|
| nhits                |     77 |         0.0989 | 0.3093 |  0.5005 |  0.8999 |                 0.2517 |      0.154  |      0.3928 |
| gbm                  |     80 |         0.1061 | 0.3292 |  0.451  |  0.8505 |                 0.2052 |      0.1641 |      0.3564 |
| sarima               |     80 |         0.1107 | 0.341  |  0.5797 |  0.9193 |                 0.1679 |      0.2025 |      0.2059 |
| har_seasonal         |     80 |         0.1218 | 0.3846 |  0.4479 |  0.8719 |                 0.0846 |      0.2227 |      0.1267 |
| prophet              |     80 |         0.1228 | 0.3761 |  0.4953 |  0.8443 |                 0.0692 |      0.2553 |     -0.0011 |
| har                  |     80 |         0.1248 | 0.394  |  0.4766 |  0.8766 |                 0.0738 |      0.2265 |      0.1121 |
| persistence          |     80 |         0.1358 | 0.4257 |  0.5318 |  0.9167 |                 0      |      0.255  |      0      |
| seasonal_persistence |     80 |         0.1549 | 0.4776 |  0.476  |  0.8703 |                -0.1733 |      0.3171 |     -0.2433 |

The hourly columns score each of the 24 target hours. cov50 and cov90 are the shares of hours that landed inside a model's 50% and 90% bands, so for well-sized bands they sit near 0.50 and 0.90. The day columns score the day's average volatility, which could be one input to a position size. day_error is the mean absolute log error of the forecast's 24-hour average against the realized average, over fully resolved days, so lower is better. Each hour's forecast in that average is its expected volatility, the middle of its band raised by the band's spread, because the average of a lopsided quantity sits above its middle and an average of 24 middles would run under the realized average. day_skill is one minus the ratio of that error to the persistence model's on the same days, so a positive value beats persistence and 1 would be a perfect forecast.

The days column is each model's own count of scored days. Models that joined the loop later are averaged over fewer days, so the rows above are not sample-matched.

The model settings changed on 2026-10-23. No forecast day made on the current settings has resolved yet, so every row above is from the settings before the change.

Matched on the 77 fully resolved days that both nhits and persistence forecast, the skill of nhits over persistence is 0.28 on the hourly pinball loss (95% interval 0.20 to 0.36) and 0.39 on the day-level error (0.21 to 0.58). Pinball loss scores the whole low-to-high forecast band, not just its middle, and lower is better. The hourly figure pools the loss over those days, while the table's skill_vs_persistence averages the 24 per-hour skills, each model over its own days. Each interval comes from the day-to-day spread of the gap between the two models' daily scores and treats each day as independent of the last. An interval that stays above zero means that, on these days, the lead over persistence is larger than day-to-day noise would explain.

The figure below is that day-level record for nhits, the current leader: its forecast of each day's average volatility, the average that realized, and the persistence model's own forecast of the same average.

![day by day: forecast, realized, persistence](figures/fig_live_daily.png)

