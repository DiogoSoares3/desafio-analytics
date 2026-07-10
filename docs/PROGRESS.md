# PROGRESS — AdventureWorks Analytics Engineering

> **Durable loop state. Lives in the repo (never temp).** The single dynamic file — update it per
> completed slice. Static conventions/decisions go in the sources of truth, not here.
> Priming read order: `.sdd/profile.md` → **this file** → latest handoff (below) →
> `PRD.md` / `ARCHITECTURE.md` as needed.

## Current status
**BUILD — Phase 2 (Dimensions), 4/7 done.** Worker #1 built + merged P2-01..P2-04 (dim_geography #4,
dim_product #5, dim_customer #6, dim_date #7); it false-stopped on a merge hiccup (PR #7 was actually
merged). Supervisor verified develop green (`dbt build` PASS=88; date-gap singular test present; docs +
surrogate keys real) and fixed P2-04 bookkeeping. Worker #2 dispatched for **P2-05/06/07** (credit_card,
sales_reason, order_status). ADRs 0001–0009; profile: subagent-per-phase.

## In review (PR open, awaiting merge) — human-review policy only
_Issues that are green with a PR open but not yet merged (`in-review`) — one line each with the PR URL.
Dependents stay blocked until their blocker here is merged (`done`). Empty under `auto-merge`, where
issues land straight to `done`._

## Latest handoff
_Path to the most recent `/handoff` file in OS temp, or "none"._

## Next actions
1. **User approves/edits the Phase-1 backlog** (backlog-review = confirm).
2. Resolve the open question below (full-data ingestion for reconciliation) — likely a Phase-3 concern,
   but confirm now so the seed strategy is right.
3. On approval: create `develop` off `main`, commit the spec baseline, then BUILD P1-01.

## Open questions
- **Full-data ingestion for the 2011 reconciliation (EL).** The seeds are tiny test fixtures. The
  $12,646,112.16 reconciliation needs the *full* `adventure_works` data in DuckDB. How does it land —
  a load script from the source Postgres, a committed Parquet/CSV export, or DuckDB reading Postgres
  directly? ARCHITECTURE marks EL "upstream/out of scope"; this is the gap. Provisionally a Phase-3
  concern (reconciliation lives with the fact), but the answer shapes the seed/data strategy now.

## Worklog (most recent first)
_One line per slice: what shipped + gate result + PR URL. Note when a human merged it (`in-review` → `done`)._
