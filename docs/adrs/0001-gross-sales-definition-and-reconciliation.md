# ADR-0001: Gross sales definition and 2011 reconciliation acceptance

> Status: accepted · Date: 2026-07-10 · Deciders: stakeholder (via /grill-me), Analytics Engineer
> Raised during PRD authoring — the CEO's audit check ($12,646,112.16 gross sales 2011) needs a precise,
> testable definition before any fact metric is built.

## Context
CEO Carlos Silveira requires proof that the model's numbers reconcile to the accounting audit, citing
2011 gross sales = **$12,646,112.16**. "Gross sales" is ambiguous (pre/post discount, with/without tax
and freight, line vs header grain), and the reconciliation tolerance was undefined. This is the trust
anchor of the whole deliverable (the régua), so it must be fixed before the sales fact is modeled.

## Decision
- **Gross sales = sum of pre-discount, pre-tax, pre-freight line revenue** — i.e. `UnitPrice × OrderQty`
  summed at sales-order-detail line level (the `SubTotal` basis, excluding tax and freight), over sales
  orders whose order date falls in the given year.
- **Acceptance test:** a dbt **singular test** that fails unless 2011 gross sales = **$12,646,112.16
  exactly (to the cent, zero tolerance)**.
- The exact source columns/formula will be confirmed empirically against the raw `adventure_works` data
  during the fact-modeling phase and locked here if they differ from the above.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Net-of-discount gross | "Gross" means before discounts; discounts are a separate KPI (promotion impact). |
| Including tax and/or freight | Inflates revenue beyond the audited figure; not the accounting basis cited. |
| Tolerance band (e.g. ±0.5%) | Régua is reconciliation/trust with a skeptic; an approximate match doesn't build trust. |
| Header-level `SubTotal` sum | Less transparent than reconstructing from line detail; harder to audit column-by-column. |

## Consequences
Fixes the grain and the metric definition for the sales fact and the "Total Sales Revenue" hero KPI.
Locks the reconciliation seam (a singular test) as a per-phase DoD gate. Updates `PRD.md` (business rule:
gross revenue definition + reconciliation acceptance) and will be referenced by `ARCHITECTURE.md` when
the fact grain and test strategy are written. Any future change to the gross definition supersedes this ADR.
