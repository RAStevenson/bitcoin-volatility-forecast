# Yesterday in review - forecast issued 2026-09-01 (generated)

**The forecast was on target.** The nhits median averaged 33% annualized volatility over the 24 hours; realized averaged 37%, 1.12x the forecast.

- 24 of 24 hours landed inside the 90% band (0 above it, 0 below). A calibrated band holds about 22 of 24.
- Across all models this was the 30th worst of 30 scored days (mean log error 0.240, median day 0.355).
- Best median that day: sarima; worst: prophet. Every model missed on the same side, so the miss is the information set, not the model choice.

Largest hourly misses (local time, America/Chicago):

| hour | forecast median | 90% band | realized | realized/forecast |
|:--|--:|--:|--:|--:|
| 2026-09-01 13:00 | 36% | 22%-67% | 64% | 1.8x |
| 2026-09-01 08:00 | 42% | 25%-76% | 68% | 1.6x |
| 2026-09-01 06:00 | 38% | 23%-68% | 27% | 0.7x |

Ratios compare annualized volatility levels, not price moves. This is a volatility review only; it says nothing about price direction.
