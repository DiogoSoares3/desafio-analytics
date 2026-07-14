# AdventureWorks Analytics Engineering

Analytics-engineering certification challenge for **Adventure Works (AW)**. Builds a reliable,
**reproducible** dimensional model over the AdventureWorks sales data (**dbt-core + DuckDB**, fully
offline), surfaced through an **Apache Superset** dashboard (BI-as-code), that answers the business
questions in [`docs/CHALLENGE.md`](docs/CHALLENGE.md) and reconciles exactly to the accounting audit
(2011 gross sales = **$12,646,112.16**).

> This README is the map for every required deliverable, where it lives, and the
> exact command to reproduce/verify it, is in [§ Deliverables map](#deliverables-map) below.

## 1. Project summary

Adventure Works wants to become data-driven, starting with the commercial (sales) area. Leadership has
six concrete business questions it can't answer reliably today (`CHALLENGE.md` a–f), the CEO
(**Carlos Silveira**) will only trust the platform if its numbers reconcile to the accounting audit, and
the Commercial Director (**Silvana Teixeira**) is a skeptic who needs to see the data move *her*
results before she buys in. The solution: all-channel (online + reseller) sales modeled as a conformed
star schema in dbt + DuckDB — tested, documented, and fully reproducible offline — surfaced through a
Superset dashboard that answers every question with the required filters, backed by an EDA notebook and
a set of commercial recommendations grounded in the same tested numbers. Full narrative:
[`docs/PRD.md`](docs/PRD.md) (Problem/Solution/Personas) and [`docs/CHALLENGE.md`](docs/CHALLENGE.md)
(the original brief).

## 2. Key results (grounded — every number below reconciles to a passing test)

| Result | Value | Where it's proven |
|---|---|---|
| 2011 all-channel gross sales (the audit anchor) | **$12,646,112.16** exact | `transform/tests/*` singular test, [ADR-0001](docs/adrs/0001-gross-sales-definition-and-reconciliation.md) |
| Total gross revenue (all years, all channels) | $110,373,889.31 | `scripts/validate_hero_kpis.py` |
| Orders / units | 31,465 orders / 274,914 units | `scripts/validate_hero_kpis.py` |
| Reseller channel | 12.1% of orders → **73.4%** of revenue (AOV $21,286 vs $1,061 online, ~20x) | `notebooks/eda.ipynb`, `bi/README.md` |
| Product mix | Bikes = **86.2%** of revenue from 32.8% of units | `notebooks/eda.ipynb` |
| Top customer | Brakes and Gears — $882,276.50 | `scripts/test_top10_customers.py` |
| Top city | Toronto — $4,498,883.73 | `scripts/validate_top5_cities.py` |
| Geography | US = 57.4% of revenue; Canada a distant #2 at $16.4M | `notebooks/eda.ipynb` |
| Question f — "On Promotion" | Top product = Water Bottle - 30 oz. (546 units); $6,361,828.95 gross | `scripts/validate_question_f.py` |
| Promotion vs. discount (Silvana's skepticism) | the real $527,507.91 discount sits entirely on the **reseller** channel, zero on online "Promotion"-tagged orders | `notebooks/eda.ipynb`, `docs/recommendations.md` #5 |

Six prioritized, numbered commercial recommendations built from these figures, framed directly for
Silvana: [`docs/recommendations.md`](docs/recommendations.md) (independently re-verified by
`scripts/test_recommendations.py`, which recomputes every cited figure from the marts rather than
trusting the doc's prose).

## 3. Prerequisites
- [`uv`](https://docs.astral.sh/uv/) (dependency manager)
- [`just`](https://github.com/casey/just) — `uv tool install rust-just`
- Docker + Docker Compose (only needed to click through the live BI dashboard — see § 5)

## 4. Setup & build (the dbt/data pipeline)
```bash
just setup        # uv sync + dbt deps (installs dbt-core, dbt-duckdb, dev tools, dbt packages)
just debug        # dbt debug -> All checks passed
just build        # seeds -> models -> tests against a local DuckDB file (offline) -- PASS=138, WARN=0, ERROR=0
just test-source  # source-layer tests only (challenge demo: `dbt test --select source:*`)
just test         # all model tests (`dbt test`)
just check        # lint + typecheck + build + tests (what CI would run)
```
The dbt project lives in [`transform/`](transform/); `just` runs dbt there against a project-local
DuckDB profile (**no cloud credentials**). The database is written to `data/adventureworks.duckdb`
(git-ignored) and is shared by the dbt models, the EDA notebook, and the BI layer. **Everything runs
offline — this is the project's dominant constraint (the "régua"): every number must reconcile to
source, and re-running `just build` must reproduce the same result.**

## 5. See the BI dashboard live (Apache Superset, Docker Compose)
```bash
just build         # if you haven't already -- creates data/adventureworks.duckdb
just bi-up         # builds + starts a local Superset container, auto-imports bi/
just bi-logs       # optional: watch the import (ready when gunicorn says "Listening at ...")
```
Open **http://localhost:8088** — login `admin` / `admin` → **Dashboards → "Adventure Works — Sales"**.
`just bi-down` stops it (keeps the imported state); `just bi-reset` wipes it for a clean re-import.
Single local container, SQLite metadata DB, DuckDB mart mounted **read-only** — no cloud, nothing
outside this machine. Full detail: [`bi/README.md`](bi/README.md).

If you'd rather not run Docker, every number on the dashboard is independently re-verified straight
against the built DuckDB file by the `scripts/validate_*.py` / `scripts/test_*.py` scripts (no live
Superset required) — see § 7.

## 6. Repository map
```
transform/            the dbt project (staging -> intermediate -> marts, medallion via dbt layers)
notebooks/eda.ipynb    EDA notebook (code + charts + commentary, reads the built DuckDB marts directly)
bi/                    Apache Superset BI-as-code bundle (databases/datasets/charts/dashboards, YAML)
bi/docker/             Dockerfile + entrypoint for the local, docker-composed Superset runtime
scripts/               outer BDD/reconciliation scripts (the "prove it" layer -- see § 7)
docs/                  PRD, ARCHITECTURE, ADRs, CHALLENGE brief, business rules, recommendations, PROGRESS
docs/adrs/              10 Architecture Decision Records -- every non-obvious modeling call, with alternatives considered
docker-compose.yml      local Superset runtime (see § 5)
justfile                single command entrypoint -- `just` lists every recipe
```

## 7. Verifying the numbers without a running Superset
Every chart/KPI on the dashboard has a companion script that reads the chart's declared SQL straight
from the committed YAML and asserts it equals a direct aggregate computed against the built DuckDB
file — proof the dashboard numbers are the tested numbers, not a parallel metric layer:
```bash
uv run python scripts/validate_hero_kpis.py          # 5 hero KPIs (Revenue, Orders, Units, AOV, Promotion-Impact)
uv run python scripts/validate_question_a.py         # question a -- orders/qty/value, 9 filter dimensions
uv run python scripts/validate_question_b.py         # question b -- top products by AOV
uv run python scripts/test_top10_customers.py        # question c -- top 10 customers
uv run python scripts/validate_top5_cities.py        # question d -- top 5 cities
uv run python scripts/validate_question_e_timeseries.py  # question e -- monthly time series
uv run python scripts/validate_question_f.py          # question f -- top product "On Promotion"
uv run python scripts/test_dashboard_bundle.py        # every chart wired into the dashboard, every filter, every metric documented
uv run python scripts/test_recommendations.py         # every recommendation cites a reconciling figure
just eda                                               # executes notebooks/eda.ipynb end-to-end, asserts required sections present
```

## Deliverables map
`docs/CHALLENGE.md` §5 lists 8 required submission items (plus one optional). Status and location of
each:

| # | Challenge requirement | Status | Where |
|---|---|---|---|
| 1 | EDA notebook (code + charts + per-insight commentary) | ✅ | [`notebooks/eda.ipynb`](notebooks/eda.ipynb) — reproduce/verify: `just eda` |
| 2 | Conceptual DW diagram (PDF), fact + dims, source tables noted | ✅ | [`docs/Star-schema.pdf`](docs/Star-schema.pdf) (exported from the Mermaid ER diagram in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#star-schema-dimensional-model)) |
| 3 | Link to the dbt repository | ✅ | this repository — `transform/` is the dbt project |
| 4 | Dashboard mockup (JPEG, Figma) | ✅ | [`docs/dashboard-mockup.jpg`](docs/dashboard-mockup.jpg) — layout mirrors the built dashboard (`bi/dashboards/adventure_works_sales.yaml`), figures illustrative |
| 5 | Power BI / Databricks AI/BI dashboard focused on commercial area | ✅ delivered as an **Apache Superset** equivalent (deliberate, justified deviation) | [`bi/`](bi/) bundle + live via `just bi-up` (§ 5); rationale + deliverable-equivalence mapping: [ADR-0002](docs/adrs/0002-bi-tool-apache-superset.md) |
| 6 | Business-rules documentation | ✅ | [`docs/business-rules.md`](docs/business-rules.md) |
| 7 | Presentation slides (project stages, EDA insights, KPI justification, dashboard walkthrough, recommendations) | ✅ | submitted as `slides.pdf` in the Moodle delivery package (not repo-tracked) |
| 8 | Demo video (3–5 min): objective, dims/fact relationships, `dbt run`/tests, dashboard walkthrough | ✅ | https://youtu.be/Y7AjVqipLPE |
| optional | Data-project plan PDF (objectives, stakeholders, risks, ROI) | ❌ | --- |

Business questions **a–f** (`CHALLENGE.md` §2) are every one answered on the dashboard with the
required filters — see the row-by-row mapping and metric definitions in [`bi/README.md`](bi/README.md).

Root Definition of Done: [`docs/PRD.md` § Definition of done](docs/PRD.md).

## 8. Decisions and rationale
Every non-obvious modeling or tooling choice is recorded as a numbered ADR, each with the alternatives
considered and why they were rejected: [`docs/adrs/`](docs/adrs/) (0001–0010). Two worth reading first
if you only read two: [ADR-0001](docs/adrs/0001-gross-sales-definition-and-reconciliation.md) (what
"gross sales" means and how the 2011 figure reconciles) and
[ADR-0010](docs/adrs/0010-sales-channel-scope.md) (why the model covers all sales channels, not just
online — discovered empirically while reconciling the audited figure).

## 9. Build process
Built via a Spec-Driven Development loop (spec → plan → build → test → record, one demoable slice at a
time). Current status, phase history, and the full worklog: [`docs/PROGRESS.md`](docs/PROGRESS.md);
per-phase plans and backlogs: [`docs/phases/`](docs/phases/).
