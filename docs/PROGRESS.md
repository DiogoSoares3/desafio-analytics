# PROGRESS — AdventureWorks Analytics Engineering

> **Durable loop state. Lives in the repo (never temp).** The single dynamic file — update it per
> completed slice. Static conventions/decisions go in the sources of truth, not here.
> Priming read order: `.sdd/profile.md` → **this file** → `PRD.md` / `ARCHITECTURE.md` as needed.

## SDD-CURSOR
- **Phase:** all 4 phases (Foundation, Dimensions, Fact, Serving) — **COMPLETE, 20/20 issues done.**
- **Doing:** none
- **Next:** none — the SDD-loop's automated backlog is fully drained.
- **Stop-reason:** none. Remaining work is outside the loop's scope: root `PRD.md`'s `FR-14`
  (slides + demo video + Figma mockup) is human-produced; `FR-15` is a Could, not required.

## Project status
`dbt build` green (PASS=138, WARN=0, ERROR=0). 2011 all-channel gross sales reconciles exactly to
**$12,646,112.16** (ADR-0001). Star schema (7 dims + `fct_sales` + `bridge_order_sales_reason`) fully
tested and documented. Superset BI-as-code bundle (`bi/`) answers business questions a–f with all
`FR-7` filters, assembled into one dashboard (`bi/dashboards/adventure_works_sales.yaml`). EDA notebook
(`notebooks/eda.ipynb`) and commercial recommendations (`docs/recommendations.md`) landed, both
independently reconciled against the built marts by outer tests. Business-rules doc
(`docs/business-rules.md`) and the conceptual DW diagram (Mermaid, in `docs/ARCHITECTURE.md`) are
written. PRD Definition of Done is checked off in `docs/PRD.md` — see there for the authoritative list.

**Outstanding (human-only, outside the loop):** `FR-14` — slides, demo video, Figma mockup.

## Phase summary
| Phase | Scope | Issues | Status |
|---|---|---|---|
| 1 — Foundation | dbt scaffolding, sources, seeds, source tests | 3/3 | done |
| 2 — Dimensions | 7 conformed dims, PK + data-quality tests | 7/7 | done |
| 3 — Fact + reconciliation | `fct_sales`, bridge, all-channel scope (ADR-0010), reconciliation tests | 5/5 | done |
| 4 — Serving | Superset BI-as-code bundle, EDA notebook, recommendations | 10/10 | done |

Full per-issue history and PR links live in `docs/phases/phase-N/backlog.md`. Key grounded figures
(re-verified independently by outer BDD tests, not just asserted): 2011 gross $12,646,112.16;
resellers = 12.1% of orders / 73.4% of revenue (~20x AOV gap); Bikes = 86.2% of gross revenue from
32.8% of units; top customer "Brakes and Gears" $882,276.4966; top city Toronto $4,498,883.7327; US =
57.4% of revenue; "On Promotion" reason = $6,361,828.95 gross (3,515 orders), while the real
`discount_amount` ($527,507.91) sits entirely on the reseller channel.

## Tactical decisions (reversible; recorded here, not ADRs)
- **Data source:** canonical public Microsoft AdventureWorks (2011–2014 dates), loaded straight into
  DuckDB/Parquet — no Postgres, no docker-compose *for data loading*. The *current* MS CSV release
  shifts dates to ~2022+; a fixed-date release is required (the 2011 reconciliation test is the oracle
  for the right dataset).
- **P3-01's table list missed `store`** (needed for reseller customer names) — extended the loader
  rather than escalating; tactical, reversible.
- **Fixed a vacuous-pass bug in `fct_sales_gross_invariant_under_bridge`** (PR #22): the test filtered
  a literal (`'Promotion'`) that matched zero rows in `dim_sales_reason` (real value: `'On Promotion'`),
  so it had passed on both-sides-`NULL` since merge without ever exercising the no-fan-out invariant.
  Found by the EDA cross-check (P4-09). Fixed the literal + added a zero-match guard so a future rename
  can't silently pass again. Landed as an orchestrator-authored fix (explicit user authorization), not
  a backlog issue, since it corrects existing merged scope rather than building new scope.
- **Superset runtime via Docker Compose** (`docker-compose.yml`, `bi/docker/`, `just bi-up`/`bi-down`/
  `bi-reset`): to let a human actually click through the dashboard (not just verify it via the outer
  BDD scripts against the DuckDB file), added a single local container — Superset + `duckdb-engine`,
  SQLite metadata DB in a named volume, DuckDB mart mounted **read-only** — that auto-imports `bi/` on
  boot. Local-only, no cloud, no extra services; does not change the dbt/DuckDB build pipeline or any
  tested number. While wiring it up, fixed a real bug in the committed
  `bi/databases/adventureworks_duckdb.yaml`: `extra` was a folded JSON **string**, but Superset's
  import schema (`ImportV1DatabaseSchema.extra`) expects a **nested YAML mapping** — the string form
  silently passed marshmallow validation error-free in review but crashed `superset import-directory`
  at runtime. Corrected to a nested mapping and added `engine_params.connect_args.read_only: true` so
  the read-only file mount doesn't error on DuckDB's default read-write open mode. This was a
  pre-existing latent bug (untriggered until a real import was attempted) rather than new scope.

## Open questions
None blocking. Project's automated scope is complete; see "Project status" above for the one remaining
human-only deliverable.

## Worklog (condensed)
- **Phase 4 (Serving)** — P4-01 Superset scaffold + hero KPIs; P4-02 question a; P4-03 question b;
  P4-04 question c (top-10 customers); P4-05 question d (top-5 cities); P4-06 question e (time
  series); P4-07 question f + Promotion-Impact hero KPI; P4-08 dashboard assembly + FR-7 filters;
  P4-09 EDA notebook; P4-10 commercial recommendations. All 10 issues landed via auto-merge PRs
  (#19–#21, #24–#29, #31–#33), each with an outer BDD test proving RED before GREEN and reconciling
  its numbers directly against the built DuckDB marts. `just build` stayed PASS=138 throughout (Phase
  4 adds no dbt models).
- **Phase 3 (Fact + reconciliation)** — P3-01 canonical AdventureWorks → DuckDB Parquet; P3-02
  `bridge_order_sales_reason`; P3-05 all-channel dim rework (ADR-0010); P3-03 `fct_sales` (order-line
  grain, 7 FKs, all channels); P3-04 the régua-headline reconciliation tests (PRs #11–#18, later
  patched by #22 — see Tactical decisions). Final `dbt build` PASS=138.
- **Phase 2 (Dimensions)** — 7/7 conformed dimensions (PRs #4–#10), `dbt build` PASS=113.
- **Phase 1 (Foundation)** — sources declared, seeds loaded, source tests green (P1-01..03).
