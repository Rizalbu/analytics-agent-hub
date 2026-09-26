# ADR-001: Funnel stage definitions & the PII boundary

**Status:** accepted

## Context

Studios disagree on what counts as a "qualified" lead: some update the lead
status field, some only create a booking. Counting stages from raw status
alone undercounts; counting bookings alone misses qualified-but-not-booked.
This definitional drift masked a real conversion drop in one city for weeks
(the scripted Crestline scenario reproduces this failure mode).

## Decision

Stage definitions live in exactly one model, `int_funnel_atomic`, and nowhere else:

| Stage | Definition |
|---|---|
| qualified | `status = 'qualified'` **OR** lead has any booking (a booking is proof of qualification) |
| booked | has a non-cancelled trial booking |
| visited | trial visit with `attended = true` |
| purchased | has a membership sale |

Stages are **cohort-attributed to the lead's creation date** and constructed
as nested subsets (`stage_x or stage_downstream`), which makes funnel
monotonicity a testable contract (`funnel_monotonicity` generic test) instead
of a hope.

Trade-off: cohort attribution means "visits in March" ≠ "visited column in
March rows" (a March visit from a February lead counts against February).
Accepted: cohort view answers the questions growth actually asks (does a
February lead convert?), and avoids double-attribution.

## PII boundary

`full_name` and `phone` exist only in `stg_leads`. Intermediate and mart
models never select them; `dim_member` carries keys and behavioral fields
only. Analysts get everything they need without a PII clearance.
