# ADR-0009: Medallion semantics via dbt-idiomatic layers

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — layering, materialization, and whether to adopt medallion
> (bronze/silver/gold) naming for traceability/governance/transparency.

## Context
The project wants medallion-style traceability, governance, and transparency (appeals to João's
governance concern and Silvana's "prove it's trustworthy" skepticism). Medallion (bronze/silver/gold) and
the dbt convention (staging/intermediate/marts) describe the **same** layering. The certification grades a
dbt/Modern-Data-Stack project, where the dbt Style Guide layout (`ref()` lineage, `source:*` tests,
staging/marts) is the expected shape.

## Decision
Keep **dbt-idiomatic folder names** as the physical layout and **document the medallion mapping** in
`ARCHITECTURE.md`:
- **Bronze (raw)** = the `adventure_works` source schema / dbt seeds — the EL landing, declared in
  `_sources.yml` (the `source:*` test seam). Not transformed.
- **Silver (cleaned/conformed)** = `staging/` (one **view** per source table `stg_adventure_works__*`:
  snake_case rename, type casts, light cleanup) + `intermediate/` (**ephemeral** joins, bridge prep,
  gross/discount business logic; not exposed).
- **Gold (business-ready)** = `marts/` — `dim_*`, `bridge_order_sales_reason`, `fct_sales` — materialized
  as **tables** (fast + stable for Superset). What the dashboard reads.

The dbt DAG/lineage graph is the traceability artifact; the mapping doc gives the governance narrative.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Rename folders literally to bronze/silver/gold | Non-idiomatic for dbt; fights dbt docs/tests/community patterns for no gain — the mapping doc captures the value. |
| Everything materialized as views | Marts recomputed per query; tables give Superset stable, fast numbers. |
| Flat single-layer project | No traceability/governance; violates the transparency goal. |

## Consequences
Delivers both the conventional dbt project the certification rewards *and* the medallion governance story
(bronze→silver→gold + dbt lineage). `staging` = the seam where the raw `adventure_works` schema is
normalized; `marts` = the tested deliverable layer. Updates `ARCHITECTURE.md` (components/layers +
materialization).
