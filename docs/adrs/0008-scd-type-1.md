# ADR-0008: SCD Type 1 (overwrite) for all dimensions

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — whether dimensions track history (Type 2) or overwrite (Type 1).

## Context
The deliverable is a point-in-time analytical snapshot answering business questions a–f. None of the
questions require an attribute's value *as of the order date* (e.g. the customer's city at purchase time)
versus its current value.

## Decision
Use **SCD Type 1 (overwrite)** for all seven dimensions — one current row per entity, no effective-dating
or versioning. Order-time attribute history is a **Won't (this version)**.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Type 2 (historical versioning) | Adds surrogate-versioning + effective-date complexity with zero payoff for questions a–f. |
| Mixed (Type 2 on select dims) | No question justifies it; inconsistent and harder to test. |

## Consequences
Simplest model that answers every question; keeps PK tests one-row-per-key (supports ADR-0007);
fully reproducible. If a future version needs order-time history, it supersedes this ADR. Updates
`ARCHITECTURE.md` (dimension strategy).
