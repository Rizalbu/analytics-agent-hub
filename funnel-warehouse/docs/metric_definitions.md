# Metric Definitions (single source of truth)

Currency is fictional Rp. All metrics computed in `mart_executive_scorecard`.

| Metric | Definition | Notes |
|---|---|---|
| `leads` | count of leads created (cohort date = creation date) | dedup'd at staging |
| `qualified` | leads with status `qualified` OR any booking | ADR-001 |
| `booked` | leads with a non-cancelled trial booking | |
| `visited` | leads whose trial was attended | |
| `purchased` | leads with a membership sale | |
| `cr_lead_qualified_pct` | qualified / leads × 100 | per month × city |
| `cr_qualified_booked_pct` | booked / qualified × 100 | |
| `cr_booked_visited_pct` | visited / booked × 100 | the no-show lever |
| `cr_visited_purchased_pct` | purchased / visited × 100 | |
| `revenue` | sum of sale `amount` (sold-date attributed) | net of discount |
| `paid_spend` | ad spend, **allocated to city by share of that city's paid leads in the month** | platforms don't report per studio; allocation documented here |
| `cac` | paid_spend / purchased | blended; paid channels only in numerator |
| `roas` | revenue / paid_spend | |
| `revenue_attainment_pct` | revenue / target_revenue × 100 | targets: seed `monthly_targets` |

**Known limitation:** CAC numerator is paid spend but denominator includes
organically-acquired members; a channel-level CAC (paid members only) is the
documented next iteration. Kept blended here to match how early-stage teams
actually report it first.
