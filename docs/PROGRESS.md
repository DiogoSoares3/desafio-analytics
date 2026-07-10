# PROGRESS — AdventureWorks Analytics Engineering

> **Durable loop state. Lives in the repo (never temp).** The single dynamic file — update it per
> completed slice. Static conventions/decisions go in the sources of truth, not here.
> Priming read order: `.sdd/profile.md` → **this file** → latest handoff (below) →
> `PRD.md` / `ARCHITECTURE.md` as needed.

## Current status
**PLAN done for Phase 1 (Foundation) — paused at backlog-confirm gate.** Both baselines validated
(2026-07-10). `docs/phases/phase-1/prd.md` + `backlog.md` written (3 issues: P1-01 scaffold →
P1-02 seeds+source → P1-03 source tests). Awaiting user approval of the backlog before BUILD.
`develop` branch not yet created. ADRs 0001–0009 accepted.

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
