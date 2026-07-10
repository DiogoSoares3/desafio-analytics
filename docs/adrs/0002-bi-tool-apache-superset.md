# ADR-0002: BI tool — Apache Superset (BI-as-code), not Power BI or Databricks AI/BI

> Status: accepted · Date: 2026-07-10 · Deciders: stakeholder + Analytics Engineer (via /grill-me)
> Raised during PRD authoring — deliverable #5 names Power BI or Databricks AI/BI; we are choosing a
> third tool and must justify the deviation and preserve deliverable-equivalence.

## Context
Challenge deliverable #5 accepts **Power BI** (`.pbix` + documented DAX) or **Databricks AI/BI** (link +
JSON). Our régua is a *graded, reproducible* deliverable, and the whole pipeline is code-first (dbt-core +
DuckDB, everything in git). The BI layer should inherit the same properties: version-controlled,
reproducible, and directly wired to the dbt marts. Power BI (`.pbix` is a binary blob, DAX is a second
metric layer divorced from dbt) and Databricks AI/BI (locks the dashboard to a live cloud workspace,
non-reproducible offline) both work against the régua.

## Decision
Use **Apache Superset** as the BI tool, in a **BI-as-code** workflow:
- Superset connects to the DuckDB marts via SQLAlchemy — the *same* models dbt builds and tests, so the
  dashboard's numbers are the tested numbers (single source of metric truth, no parallel DAX layer).
- Datasets, charts, and dashboards are **exported as YAML and committed to git** — versioned, diffable,
  reproducible, re-importable by a grader.
- **Deliverable-equivalence is mandatory:** we produce the Superset analogues of exactly what Power BI /
  Databricks AI/BI submissions provide — the exported **dashboard bundle (YAML/JSON)** (analogue of the
  `.pbix` / Databricks JSON), a **link/how-to-run** (analogue of the AI/BI link), and documented metrics
  (analogue of documented DAX measures — here the dbt/Superset dataset definitions). Screenshots and the
  demo video cover the visual walkthrough.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Power BI (`.pbix` + DAX) | Binary artifact not diffable in git; DAX is a second metric layer decoupled from the tested dbt models; weaker reproducibility. |
| Databricks AI/BI | Dashboard bound to a live cloud workspace; not reproducible offline; against the régua. |
| Superset + Power BI hedge | Doubles BI effort and splits metric truth; the deviation is defensible on its own with equivalent exports. |

## Consequences
Deviates from the literal submission format (#5), so **adherence risk** exists with a strict grader.
Mitigations: (1) export the equivalent artifacts listed above; (2) justify the BI-as-code choice
explicitly in the slides as part of the data-driven-culture argument (reproducibility, git history,
metric-consistency with the tested models); (3) include screenshots + the demo video. Unlocks a fully
code-first, git-versioned BI layer whose numbers are guaranteed consistent with the reconciled dbt marts.
Updates `PRD.md` (dashboard requirement + deliverable-equivalence note).
