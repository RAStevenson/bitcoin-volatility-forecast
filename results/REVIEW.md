# Yesterday in review - forecast issued 2026-11-14 (generated)

**The forecast was too low.** The nhits forecast averaged 32% annualized volatility over the 24 hours; realized averaged 84%, 2.62x the forecast. The forecast counts as on target when the realized volatility averages within a factor of 1.5 of the forecast, above or below it.

- 9 of 24 hours landed inside the 90% band (15 above it, 0 below). A calibrated band holds about 22 of 24.
- Across all models the day's mean absolute log error was 0.912, the 2nd largest of 103 scored days (median day 0.353).
- Among the models, seasonal_persistence had the smallest mean absolute log error that day and prophet the largest. Every model forecast too low, so the error traces to what was knowable that day rather than to any one model's choice.

Largest hourly errors (local time, America/Chicago):

| hour | forecast median | 90% band | realized | realized/forecast |
|:--|--:|--:|--:|--:|
| 2026-11-14 16:00 | 30% | 17%-61% | 154% | 5.1x |
| 2026-11-14 19:00 | 31% | 16%-61% | 149% | 4.8x |
| 2026-11-14 20:00 | 30% | 16%-61% | 138% | 4.7x |

Ratios compare annualized volatility levels, not price moves. This is a volatility review only; it says nothing about price direction.

## The daily forecast's own claims

On the most recent resolved day the daily forecast called the day normal and falling; it turned out high and rising. The one-standard-deviation day move was 1.6% and the price ended 2.5% from where it started, outside that distance. 0 of the 3 loudest hours named were among the day's 3 loudest, and 0 of the 3 calmest. 0.0 hours were expected to run high and 15 did.

Over 103 resolved days, scored in the terms the daily forecast states them, with what repeating yesterday would have scored beside each claim:

- The price ended inside the one-standard-deviation day move on 69 of 103 days (67%). A well-sized move holds about 68% of days. The same distance taken from yesterday's realized hours would have held on 76.
- The regime word (quiet, normal, elevated, high) matched the realized day on 70 of 103 days, was one step off on 30, and two or more steps off on 3. Repeating yesterday's word would have matched on 64.
- The trend word (rising, steady, falling) matched on 63 of 103 days. Always saying steady would have matched on 33.
- Of the 3 loudest hours named each day, 1.3 on average were among the day's 3 loudest, and 0.7 of the 3 calmest. Naming yesterday's loudest and calmest hours again would have scored 1.0 and 0.5; naming 3 hours at random, 0.4.
- 108 hours were expected to run high across those days and 147 did. Yesterday's count, carried forward, would have expected 133.
