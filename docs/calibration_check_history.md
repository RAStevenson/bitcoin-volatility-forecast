# How the calibration check came to its current form

This is the record of the check's first version, why it was replaced,
and which models the current version has flagged. The README describes
the check as it works now, and its Models section says what each named
model is.

`LIVE.md` carries a `cov90` column, the fraction of hours where the
realized value landed inside a model's 90% band. A calibrated model
sits near 0.90, and a model that sits well below it is claiming more
precision than it has.

The first version of the check compared that column against a fixed
floor of 0.80 and named anything underneath. The check also had a 0.98
ceiling, which no model came near while it was active. From
2026-08-16 to 2026-08-24 the check named `gbm` every day, and from 2026-08-20 on the list
grew to three to five of the eight models. The list never emptied, so
the check carried no information. A signal that is always on cannot
tell you when something changed. Its widest list came on 2026-08-21,
when it named five models.

The problem was that the floor sat inside the noise. Hours within a
day move together, so 24 hourly rows carry about one day's worth of
independent evidence, and the sample that matters is the number of
scored days, not the row count. At 21 scored days, a typical model's
day-level coverage has a standard error of about 0.045, the noise
expected in that average from 21 days alone. The gap between the 0.80
floor and the 0.90 target is roughly two standard errors wide. For a
model whose true coverage sits anywhere in the 0.80s, which side of the
floor its estimate lands on is decided by noise. The membership of the
flagged list showed exactly that. On 2026-08-24, `seasonal_persistence`
left the list at 0.8056 while `har_seasonal` stayed on it at 0.7956.
Those two numbers are 0.01 apart, against a standard error of 0.045. The t
statistic counts a model's shortfall below 0.90 in standard errors, so
more negative is stronger evidence. Of the two, `seasonal_persistence`
had the stronger evidence of coverage below target (t = -2.15 against
-1.89), because its day-to-day spread was tighter.
`har` appeared for two days and left. `seasonal_persistence` appeared
for four days and left. Nothing about those models had changed.

Since 2026-08-24 the check tests the evidence instead of the bare
average. It takes each model's coverage one day at a time and runs a
two-sided t-test of those daily figures against 0.90, asking whether
their average sits farther from 0.90, in either direction, than their
own spread explains. A test rejects when it does, and the level is the
false-alarm rate accepted per test, 5%. The check divides that 5% by
the number of models tested (a Bonferroni correction), because eight
tests at 5% each would raise a false alarm often. A model is flagged
only after it rejects on three consecutive scored days, so a single
noisy day cannot raise an alarm and a real departure still surfaces
within days. A shorter streak is reported as pending. Earlier results are recomputed from `evaluation.csv`, the
log of every scored forecast, rather than stored, so the whole check is
reproducible from that log with no state file that could drift out of
step with the data.

Replayed over every scored day, the check stayed silent through
2026-08-30, and not by a wide margin. `gbm` rejected on 2026-08-26 and
2026-08-27, `prophet` on 2026-08-27 and 2026-08-28, and each streak
broke one day short of a flag. A fresh `gbm` streak began on
2026-08-29. On 2026-08-31 the check flagged a model for the first time.
It named `gbm`, whose coverage over its 28 scored days was 0.7932. The
p-value is the chance of a gap that large, in either direction, arising
from noise alone. For `gbm` it was 0.0058, under the corrected
threshold of 0.0063, which is 5% divided by the eight models tested.
`gbm` was the model
nearest the line when the check was rebuilt, so the first flag landing
on it reads as the check doing what it was rebuilt to do. That flag
lasted one run and cleared on 2026-09-01. `prophet` was then flagged
from 2026-09-04 through 2026-09-07, and no model has been flagged
since, as of 2026-10-01. The bands stay as each model produces them,
and LIVE.md's git history is the published record of when they ran too
narrow.
