# SDD Project Profile — AdventureWorks Analytics Engineering

> Layer 2. The **only** file that changes between projects. The plugin's `/sdd` skill reads this to
> parametrize the invariant methodology. Keep it lean; fill every slot.

## Régua (dominant constraint)
Graded, reproducible deliverable — every number must reconcile to source (e.g. 2011 gross sales =
$12,646,112.16, per the CEO's audit check) and a grader must be able to re-run the whole pipeline
offline and get the same result. When correctness/reconciliation conflicts with scope or speed,
reconciliation wins.

## Sources of truth
| Artifact | Path | Validated by |
|---|---|---|
| Product truth | `docs/PRD.md` | stakeholders (challenge business questions a–f + KPI/dashboard requirements) |
| Technical truth | `docs/ARCHITECTURE.md` | devs (dimensional model, dbt layering, seams, tests) |

## Spec gate (hard stop before any build)
`docs/PRD.md` validated against the CHALLENGE.md business questions (a–f), KPIs, and deliverables AND
`docs/ARCHITECTURE.md` validated for the dimensional model (fact + dimensions, source→mart lineage, dbt
layering, seams, test strategy). No dbt models are built before both are validated.

## Vertical slice (what a tracer bullet cuts through)
`raw source (seed) → staging model → dim/fact mart → dbt tests (source + PK + data-quality + reconciliation)
→ documentation → one answered business question / dashboard tile`. A slice is demoable when its mart
runs green and the number it produces reconciles to source.

## Issue granularity (one demoable tracer bullet; ~300 LOC anchor)
The unit is **one thin, demoable behaviour** end-to-end — typically one staging→mart lineage path that
lights up one business question or one KPI, with its tests. **~300 LOC** (SQL + YAML tests + docs) is the
default anchor, not a hard limit. A single dimension or the fact grain is usually one slice; split a mart
that answers multiple questions, merge trivially small seed/staging pairs. Régua + demoability win on
conflict.

## Seams (where tests intercept behavior)
Prefer existing, highest, fewest:
- **dbt sources** (`source:*` freshness/shape tests on the seeded raw layer),
- **model contracts + schema tests** (PK `unique`+`not_null`, relationships, accepted values),
- **singular / reconciliation tests** (SQL assertions, e.g. gross sales 2011 = audited figure).
These three are the interception points `/bdd` + `/tdd` target.

## Fakes / fixtures (no live infra in tests)
**dbt seeds** — tiny curated CSV fixtures of the `adventure_works` tables under test, loaded into local
DuckDB. No cloud, no live Postgres/Databricks: `dbt build` runs the seeds → models → tests entirely
offline. Reconciliation tests that need the full audited figures run against the full local dataset,
kept separate from the seed-based unit fixtures.

## Definition of Done (per-phase gates)
- `dbt build` green (models run + all tests pass) against local DuckDB.
- `dbt test --select source:*` green (source tests pass).
- PK tests (`unique` + `not_null`) pass on every dim and fact.
- Data-quality tests (accepted values, relationships, not_null on required fields) pass.
- Any audited number in the slice's scope reconciles to source (reconciliation test green).
- Tables and columns in the touched data marts are documented (dbt `description:`).
- The slice's business question / KPI can be answered from the resulting model.

## Phase-cutting rule
Cut phases by **dependency order along the lineage**, one seam group per phase where possible:
1. Foundation — dbt project scaffolding, sources declared, seeds, source tests.
2. Dimensions — build each conformed dimension (product, customer, date, geography, card type, sales
   reason, status) with PK + data-quality tests.
3. Fact — sales fact at the agreed grain, joins to dims, metrics, reconciliation to audited figures.
4. Serving — EDA notebook, KPIs, dashboard tiles answering business questions a–f.
A Must that depends on a Should still waits on its blocker (MoSCoW prioritizes, dependency order sequences).

## Test command(s)
- `dbt build` — run models + all tests against local DuckDB (the primary green signal).
- `dbt test --select source:*` — source-layer tests (required by the challenge demo).
- `dbt test` — all model tests.

## Loop
- **Acceptance scenarios:** issues carry a Gherkin `Scenario:` (authored via `/bdd`), realized as the
  outer behaviour test using the seam/mechanism named in `ARCHITECTURE.md`/ADRs — for this project a dbt
  singular/schema test asserting the slice's number or shape. No matrix here — the arch doc owns "how a
  behaviour is tested in this project".
- **Fresh-agent mode:** `subagent` — spawn a fresh agent per issue **in its own git worktree on the issue
  branch**. Uses the branch-per-issue flow below.
- **Handoff mode:** `auto` — self-continuing via a flat supervisor that respawns sequential worker
  subagents from files + handoff. Requires subagent support (available in this host). Files + handoff are
  the durable state; the context gate is a checkpoint, not a stop.
- **Backlog review:** `confirm` — pause after `/to-issues` and surface the phase backlog for approval/edit
  before building. The two baselines stay the only human-validated docs; this is a gate on the derived layer.
- **Integrity enforcement:** `prose+git+verifier` — immutable scenario, RED proof, test-first commit,
  clean re-run, **plus** an independent verifier agent re-reads the branch/PR diff for test-gaming
  (justified by the reconciliation-heavy régua). Escalate uncovered critical decisions via `/grill-me` → ADR/PRD.

## Git strategy (branch-per-issue)
- **Protected branch:** `main` — the loop **never** commits here (human-only `develop → main` promotion).
- **Integration branch:** `develop` — every issue lands here; dependents branch off it once the blocker lands.
- **Issue branch naming:** `issue/<id>-<slug>`.
- **PR provider:** `gh` (GitHub CLI, authenticated as DiogoSoares3).
- **Merge policy:** `auto-merge` — open a GitHub PR per issue and merge it when checks pass, no human gate;
  the backlog drains straight to `done`.
- **Backlog statuses:** `todo → doing → done`.

## Paths
- **Phases dir:** `docs/phases/` — each epic gets `docs/phases/phase-N/` holding **`prd.md`** (the phase
  projection) and **`backlog.md`** (that phase's issues). Deterministic dir name `phase-N` (N = phase
  number); the epic's human name lives in the `prd.md` H1.
- **Baselines:** root PRD `docs/PRD.md` · technical truth `docs/ARCHITECTURE.md` · ADRs `docs/adrs/`.
- **Durable state:** `docs/PROGRESS.md` — the single **global** loop cursor (phase/issue, latest handoff).
  One file, never per-phase.
- **Templates:** root PRD for `/to-prd` = skill default; phase PRD (filled by PLAN) =
  `templates/prd/phase-PRD.template.md`.
