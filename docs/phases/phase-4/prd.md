# Phase 4 — Serving

> **Derived layer** (assistant's phase projection — not separately grilled). Projects the validated
> baselines: root [`PRD.md`](../../PRD.md) by requirement ID, [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
> by seam. Does **not** restate Problem/Solution. Phase-cutting rule: profile §Phase-cutting step 4
> (Serving) — the last phase; Phases 1–3 (Foundation, Dimensions, Fact) are `done`.

## Realizes (requirement IDs)
`FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, NFR-3` (partially `NFR-4` — BI bundle documentation/versioning).

- `FR-6` — answer business questions a–f (`CHALLENGE.md`) from the model via the Superset dashboard.
- `FR-7` — dashboard filters: product, card type, sales reason, order date, customer, order status,
  city, state, country, **sales channel (online/reseller)**.
- `FR-8` — core commercial KPIs, with **Total Revenue, AOV, and Promotion-impact as hero KPIs**.
- `FR-9` — Superset deliverable-equivalence exports: committed dashboard/dataset **YAML/JSON bundle**,
  run instructions, documented metric definitions.
- `FR-10` — actionable commercial recommendations for AW, framed for Silvana (grading criterion 6).
  *[manual/external]*
- `FR-11` — EDA notebook (code, charts, per-insight commentary). *[manual/external]* — called out
  explicitly by the profile's phase-cutting rule as part of "Serving".
- `NFR-3` — dashboard numbers are the *tested* model numbers (Superset reads the same DuckDB marts, no
  parallel metric layer); every question a–f answerable with the required filters.

## Capabilities in scope
Root `PRD.md` MoSCoW rows realized here:
- **Must** — "Superset dashboard answering business questions a–f with all required filters" (`FR-6, FR-7,
  NFR-3`).
- **Must** — "Core commercial KPIs (heroes: Total Revenue, AOV, Promotion-impact)" (`FR-8`).
- **Must** — "Superset deliverable-equivalence exports (dashboard YAML/JSON bundle + run instructions +
  documented metrics)" (`FR-9`).
- **Must** — "Actionable commercial recommendations for AW, framed for Silvana" (`FR-10`)
  *[manual/external]*.
- **Should** — "Exploratory Data Analysis notebook" (`FR-11`) *[manual/external]*.

## Seam(s) touched
- **BI (Apache Superset, [ADR-0002](../../adrs/0002-bi-tool-apache-superset.md))** — Superset connects to
  the DuckDB marts (`dim_*`, `bridge_order_sales_reason`, `fct_sales`) via SQLAlchemy; datasets, charts,
  and the dashboard are exported as **YAML** under `bi/` and committed (ARCHITECTURE.md §BI /
  §deliverable-equivalence). This is the phase's primary seam — no new dbt transform logic is required
  (Phase 3 already exposes every measure/attribute FR-6–FR-8 need); the seam is "does the chart/KPI
  reconcile to the already-tested mart number".
- **`ARCHITECTURE.md` §Star schema** — `fct_sales` + 7 dims + `bridge_order_sales_reason` are the sole
  data source for every chart; no parallel metric layer (`NFR-3`).
- **EDA notebook seam (`notebooks/`)** — reads the same built DuckDB marts (not a separate extract);
  Python is a thin layer per `CLAUDE.md` conventions.
- **Manual/external artifacts** (`FR-10`) — a markdown/PDF recommendations doc citing dashboard/EDA
  figures; not a dbt/Superset build artifact, so it has no schema/singular-test seam — its acceptance
  scenario is authored (via `/bdd`) as an outer demoable check instead (see backlog).

## Depends on
- **Phase 3 (Fact + reconciliation)** — `done`. `fct_sales` (order-line grain, all channels, 7 dim FKs,
  `is_online`) and `bridge_order_sales_reason` are built, green, and reconcile exactly to the audited
  2011 figure. Phase 4 builds no new dbt models — it is a pure read-only serving layer over Phase 2–3's
  Gold marts.

## DoD gate (this phase)
Subset of the root Definition of Done this phase satisfies (root `PRD.md` §Definition of done, items
5 and 6), plus phase-specific checks:
- The Superset dashboard answers all six business questions (a–f), each traceable to the exact
  `CHALLENGE.md` wording, with the required filters (product, card type, sales reason, order date,
  customer, order status, city, state, country, sales channel).
- Hero KPIs (Total Revenue, AOV, Promotion-impact) are presented and reconcile to the tested `fct_sales`
  aggregates (no parallel metric layer — `NFR-3`).
- The deliverable-equivalence bundle exists: committed dataset/chart/dashboard YAML under `bi/`, run
  instructions (how a grader re-imports/re-runs it locally), and documented metric definitions.
- The EDA notebook exists under `notebooks/`, runs end-to-end against the built marts with no errors,
  and includes commentary per insight.
- Actionable, prioritized commercial recommendations for AW exist, framed for Silvana, each citing a
  specific reconciled number from the model/dashboard/EDA.
- Nothing in this phase regresses Phase 1–3's green signal (`dbt build` / `dbt test --select source:*`
  stay green — Phase 4 adds no dbt models, so this is a non-regression check, not new build surface).

## Deferred to later phases
None within the SDD loop — Phase 4 is the last phase per the profile's phase-cutting rule (Foundation →
Dimensions → Fact → Serving).

**Out of the SDD loop's automated scope** (root `PRD.md` still lists these for the actual challenge
submission, but they are pure manual/external artifacts with no dbt/BI seam a build worker can test —
`FR-12` business-rules documentation, `FR-13` conceptual DW diagram PDF, `FR-14` slides + demo video +
Figma mockup, `FR-15` *(Could)* data-project plan PDF). These are not cut into this phase's backlog;
they are produced by the human directly against the root PRD's Definition of Done, outside the
issue/BDD/TDD loop.
