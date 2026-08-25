# Yesterday in review - forecast issued 2026-08-24 (generated)

**The forecast was too low.** The nhits median averaged 27% annualized volatility over the 24 hours; realized averaged 56%, 2.05x the forecast.

- 23 of 24 hours landed inside the 90% band (1 above it, 0 below). A calibrated band holds about 22 of 24.
- Across all models this was the 9th worst of 22 scored days (mean log error 0.502, median day 0.402).
- Best median that day: persistence; worst: prophet. Every model missed on the same side, so the miss is the information set, not the model choice.

Largest hourly misses (local time, America/Chicago):

| hour | forecast median | 90% band | realized | realized/forecast |
|:--|--:|--:|--:|--:|
| 2026-08-24 21:00 | 22% | 10%-65% | 120% | 5.4x |
| 2026-08-25 02:00 | 19% | 8%-66% | 64% | 3.4x |
| 2026-08-25 04:00 | 19% | 8%-79% | 62% | 3.2x |

Ratios compare annualized volatility levels, not price moves. This is a volatility review only; it says nothing about price direction.
