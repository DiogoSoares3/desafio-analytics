# PRD — AdventureWorks Analytics Engineering

> **VALIDATED (stakeholder) — 2026-07-10.** Product truth (what / why / scope / priority). The technical "how" — dimensional grain, dbt layering,
> seams, test mechanism — lives in `ARCHITECTURE.md`; it is referenced, not duplicated.
> Decisions already closed: [ADR-0001](adrs/0001-gross-sales-definition-and-reconciliation.md) (gross
> sales definition + 2011 reconciliation), [ADR-0002](adrs/0002-bi-tool-apache-superset.md) (BI tool =
> Apache Superset). Analytical minimum = business questions a–f in [`CHALLENGE.md`](CHALLENGE.md).

## Problem
Adventure Works wants to become data-driven, starting with the **commercial (sales) area**. Leadership
has concrete questions (a–f) it cannot answer reliably today, and the project lacks unanimous support:
the **Commercial Director, Silvana Teixeira, is a skeptic** — she'd rather spend on promotions and has
been burned by past "data-driven" promises. The CEO will only trust the platform if its numbers
**reconcile to the accounting audit** (2011 gross sales = $12,646,112.16). So the product must
simultaneously (1) answer the business questions, (2) prove its numbers are trustworthy, and (3) convert
a skeptical commercial leader by showing data that moves *her* results.

## Solution
A reliable, reproducible **dimensional model over the `adventure_works` sales data — all channels
(online + reseller)** (dbt-core + DuckDB, fully testable offline), surfaced through an **Apache Superset
dashboard (BI-as-code)** that answers questions a–f with the required filters (including a **sales
channel** filter) and foregrounds a small set of commercial KPIs. Trust is earned by an **exact
reconciliation test** to the audited 2011 figure plus source/PK/data-quality tests.

> **Scope resolved empirically (2026-07-11).** The audited 2011 gross `$12,646,112.16` is the sum over
> **all** sales channels (online $3.86M + reseller $8.78M); online-only totals $3.86M and does not
> reconcile. Per this PRD's own rule — *"the 2011 reconciliation figure defines the exact included set"*
> — v1 scope is **all sales**, with **channel (online/reseller) as a filterable attribute** so the
> commercial view can still foreground online. Supersedes the earlier online-only assumption. See
> [ADR-0010](adrs/0010-sales-channel-scope.md).
The story delivered to Silvana: concrete, filterable, audited numbers about *her* products, customers,
cities, and promotions — plus actionable recommendations.

## Personas & user stories

### Primary — Silvana Teixeira, Commercial Director (skeptic to convert)
Every KPI and view must answer "what does this do for commercial results?" She trusts numbers she can
filter and verify, and has been burned by past "data-driven" promises.
1. As the Commercial Director, I want to see total revenue, orders, and units sliced by product,
   customer, city/state/country, card type, sales reason, and status, so that I can find where
   commercial results are actually coming from. *(FR-6, FR-7, FR-8)*
2. As the Commercial Director, I want to know which products have the highest average order value by
   period and geography, so that I can steer the mix toward higher-value sales. *(FR-6b, FR-8)*
3. As the Commercial Director, I want my top-10 customers and top-5 cities by revenue, with filters, so
   that I can focus commercial effort where it pays off. *(FR-6c, FR-6d)*
4. As the Commercial Director, I want to see revenue and volume trend by month and year, so that I can
   judge seasonality and momentum instead of guessing. *(FR-6e)*
5. As the Commercial Director, I want to see which product sells the most units under the "Promotion"
   sales reason and the overall discount/promotion impact, so that I can compare data-driven decisions
   against my instinct to just spend on promotions. *(FR-6f, FR-8)*
6. As the Commercial Director, I want concrete, prioritized recommendations drawn from the data, so that
   I can act — not just look at charts. *(FR-10)*

### Secondary — Carlos Silveira, CEO (trust gate)
7. As the CEO, I want proof that the model's 2011 gross sales equals the audited $12,646,112.16, so that
   I can trust every other number the platform produces. *(FR-3, NFR-2)*
8. As the CEO, I want the whole pipeline to re-run and reproduce the same figures, so that data becomes a
   dependable long-term strategic asset, not a one-off report. *(NFR-1)*

### Secondary — João Muller, Innovation Director (sponsor / ROI)
9. As the Innovation Director, I want a documented, tested, version-controlled model, so that the
   platform is extensible to other areas and defensible on cost/timeline. *(FR-4, FR-5, NFR-4)*
10. As the Innovation Director, I want the deliverable to demonstrate clear ROI and value narrative
    (incl. the risks/contingencies plan), so that I can sustain executive support for the project.
    *(FR-10, FR-15)*

### Secondary — Gabriel Santos, Data Analyst / IT (data gatekeeper)
11. As the IT data analyst, I want dimensions and facts that are documented and tested, so that I can
    trust them and stop fielding repetitive ad-hoc SQL requests from business units. *(FR-4, FR-5)*
12. As the IT data analyst, I want the transformations expressed as reproducible, reviewable code in a
    repository, so that data access and lineage are transparent and auditable. *(NFR-1, NFR-4)*

## Scope & prioritization (MoSCoW)
Every capability sits in exactly one bucket. **Won't (this version)** *is* the out-of-scope list.
> **Built vs manual:** dbt builds/tests the model, KPIs, and Superset dashboard. Items tagged
> **[manual/external]** are produced by the Analytics Engineer outside the codebase (not built or tested
> by dbt) — the EDA notebook, business-rules doc, conceptual DW diagram, mockup, slides, video.

| Priority | Capability | Requirements |
|---|---|---|
| **Must** | Conformed dimensional model over `adventure_works` sales — **all channels** (7 dims + sales fact), with online/reseller channel as a filterable attribute | FR-1, FR-2, NFR-1 |
| **Must** | Exact 2011 gross-sales reconciliation to $12,646,112.16 (per ADR-0001) | FR-3, NFR-2 |
| **Must** | Source tests, PK tests, and data-quality tests all green | FR-4, NFR-2 |
| **Must** | Model + column documentation in the data marts | FR-5, NFR-4 |
| **Must** | Superset dashboard answering business questions a–f with all required filters | FR-6, FR-7, NFR-3 |
| **Must** | Core commercial KPIs (heroes: Total Revenue, AOV, Promotion-impact) | FR-8 |
| **Must** | Superset deliverable-equivalence exports (dashboard YAML/JSON bundle + run instructions + documented metrics), per ADR-0002 | FR-9 |
| **Must** | Actionable commercial recommendations for AW, framed for Silvana **[manual/external]** | FR-10 |
| **Should** | Exploratory Data Analysis notebook (code + charts + insight commentary) **[manual/external]** | FR-11 |
| **Should** | Business-rules documentation **[manual/external]** | FR-12 |
| **Should** | Conceptual DW diagram (PDF) with source→mart lineage **[manual/external]** | FR-13 |
| **Should** | Presentation slides + demo video + Figma mockup **[manual/external]** | FR-14 |
| **Could** | Data-project plan PDF (objectives, stakeholders, risks/ROI — addresses Silvana's skepticism) **[manual/external]** | FR-15 |
| **Won't (this version)** | Integration of other source systems (SAP / Salesforce / Google Analytics / WordPress) — conceptual mention only | — |
| **Won't (this version)** | Cloud deployment (Databricks / dbt Cloud) — local DuckDB is the reproducible target | — |
| **Won't (this version)** | Power BI or Databricks AI/BI dashboards (superseded by Superset, ADR-0002) | — |
| **Won't (this version)** | Forecasting / ML / predictive metrics (descriptive analytics only) | — |

> Priority is the **stakeholder signal** for what matters most. Execution **order** is still
> dependency-driven (dims before fact before dashboard) — MoSCoW prioritizes, it does not sequence.

## Requirements

### Functional (FR-n)
- `FR-1` — Model **seven conformed dimensions**: product, customer (individual **and** store customers —
  reseller orders are store-backed), date, geography (city/state/country), credit-card (card type; with an
  **"N/A" member** for reseller lines that have no card), sales reason, order status. *(Sales-reason is
  many-to-many with orders — resolution flagged for `ARCHITECTURE.md`.)*
- `FR-2` — Model a **sales fact** at the agreed grain over **all sales orders (online + reseller)**,
  joinable to all seven dimensions, exposing order count, quantity, gross revenue, discount, and net
  revenue metrics, and carrying **sales channel (online/reseller via `OnlineOrderFlag`) as a filterable
  attribute** so the commercial view can foreground online.
- `FR-3` — Compute **gross sales** as pre-discount, pre-tax, pre-freight line revenue (`UnitPrice ×
  OrderQty` at line level) per ADR-0001, and **reconcile 2011 gross sales to $12,646,112.16 exactly
  (zero tolerance)** via an automated test.
- `FR-4` — Provide **source tests**, **primary-key tests** (`unique` + `not_null` on every dim and the
  fact), and **data-quality tests** (accepted values, relationships, required not-nulls) — all passing.
- `FR-5` — **Document** every mart table and column (descriptions) so a grader/analyst understands each field.
- `FR-6` — Answer **business questions a–f** (CHALLENGE.md) from the model via the dashboard:
  orders/quantity/value by many slices (a); top products by AOV over time & geography (b); top-10
  customers (c); top-5 cities (d); orders/quantity/value time series by month & year (e); top product by
  units for the "Promotion" sales reason (f).
- `FR-7` — Provide **dashboard filters** for product, card type, sales reason, order date, customer,
  order status, city, state, country, and **sales channel (online/reseller)**.
- `FR-8` — Present the **core commercial KPIs**: Total Sales Revenue, Number of Orders, Units Sold,
  Average Order Value (gross − discounts ÷ orders), Top Products/Customers/Cities by revenue, revenue
  trend by month/year, and promotion (discount) impact — with **Total Revenue, AOV, and Promotion-impact
  as hero KPIs**.
- `FR-9` — Produce **Superset deliverable-equivalence exports** (ADR-0002): committed dashboard/dataset
  **YAML/JSON bundle** (analogue of `.pbix` / AI-BI JSON), **run instructions/link**, and **documented
  metric definitions** (analogue of documented DAX).
- `FR-10` — Produce **actionable commercial recommendations** for AW derived from the model/EDA, framed
  for Silvana (grading criterion 6). *[manual/external]*
- `FR-11` — Produce an **EDA notebook** (code, charts, per-insight commentary). *[manual/external]*
- `FR-12` — Produce **business-rules documentation**. *[manual/external]*
- `FR-13` — Produce a **conceptual DW diagram (PDF)** noting source tables per dim/fact. *[manual/external]*
- `FR-14` — Produce **slides + demo video (≤10 min) + Figma mockup**. *[manual/external]*
- `FR-15` — *(Could)* Produce a **data-project plan PDF** (objectives, stakeholders, risks/contingencies,
  ROI narrative addressing commercial skepticism). *[manual/external]*

### Non-functional (NFR-n)
- `NFR-1` — **Reproducible offline:** the entire model builds and tests green via local dbt-core + DuckDB
  with seeded fixtures — no cloud, no live DB — so a grader re-runs it and reproduces every number.
- `NFR-2` — **Trustworthy:** `dbt build` green (models + all tests); `dbt test --select source:*` green;
  the 2011 reconciliation exact. A single failing test fails the deliverable.
- `NFR-3` — **Answerable & consistent:** dashboard numbers are the *tested* model numbers (Superset reads
  the same DuckDB marts — no parallel metric layer), and every question a–f is answerable with the
  required filters.
- `NFR-4` — **Documented & version-controlled:** models, columns, and the Superset dashboard bundle are
  documented and committed to the git repository (GitHub link is a deliverable).

## Definition of done
v1 is done when **all** boxes below are checked.

- [x] `dbt build` runs **green offline** (grader reproduces every number). *(NFR-1, NFR-2)*
- [x] **2011 gross sales reconciles to $12,646,112.16 exactly** (ADR-0001 test green). *(FR-3)*
- [x] Source, PK (unique+not_null on all dims+fact), and data-quality tests all pass. *(FR-4)*
- [x] All marts (dims + fact) are documented. *(FR-5)*
- [x] The Superset dashboard answers all six business questions (a–f) with the required filters, and the
      deliverable-equivalence exports exist. *(FR-6, FR-7, FR-8, FR-9)*
- [x] Actionable commercial recommendations for AW are produced, framed for Silvana. *(FR-10)*
- [x] EDA notebook (code, charts, per-insight commentary). *(FR-11)* — `notebooks/eda.ipynb`
- [x] Business-rules documentation. *(FR-12)* — `docs/business-rules.md`
- [x] Conceptual DW diagram with source→mart lineage. *(FR-13)* — `docs/ARCHITECTURE.md` star-schema
      Mermaid diagram (PDF)
- [x] Dashboard mockup (JPEG). *(FR-14, part)* — `docs/dashboard-mockup.jpg`
- [ ] Presentation slides + demo video (≤10 min). *(FR-14, part)*
- [ ] *(Could)* Data-project plan PDF (objectives, stakeholders, risks/contingencies, ROI narrative).
      *(FR-15)*

## Notes
- **Channel:** v1 is **all sales** (online + reseller). Confirmed empirically 2026-07-11: 2011 all-sales
  gross = `$12,646,112.16` (matches the audit) vs online-only `$3,863,120.21` (does not); per this PRD's
  rule the reconciliation figure defines the included set → all channels. `OnlineOrderFlag` is retained
  as a **filterable channel attribute** on the fact so the commercial view can foreground online.
  See [ADR-0010](adrs/0010-sales-channel-scope.md).
- **Open questions:** none remaining. The four engineer-owned questions raised for
  `ARCHITECTURE.md` — (1) sales-reason many-to-many resolution and its effect on question f
  ("Promotion"), (2) exact fact grain (line vs header), (3) date-spine range, (4) geography
  conformance across customer/ship-to addresses — are resolved in `ARCHITECTURE.md` via
  [ADR-0003](adrs/0003-sales-reason-multi-valued-bridge.md),
  [ADR-0004](adrs/0004-sales-fact-grain-order-line.md), [ADR-0006](adrs/0006-date-spine.md), and
  [ADR-0005](adrs/0005-geography-conformance-ship-to.md) respectively.
- **Cross-references:** [ADR-0001](adrs/0001-gross-sales-definition-and-reconciliation.md),
  [ADR-0002](adrs/0002-bi-tool-apache-superset.md).
