# AdventureWorks Analytics Engineering — task runner
# Prefer `just <recipe>`. Run `just` with no args to list recipes.

# The dbt project lives in transform/; run all dbt commands against it.
dbt_dir := "transform"
export DBT_PROFILES_DIR := "transform"
# Local DuckDB lives in data/ (absolute path -> deterministic regardless of cwd).
export DBT_DUCKDB_PATH := justfile_directory() / "data" / "adventureworks.duckdb"

# List available recipes
default:
    @just --list

# Install Python deps (dbt + dev tools) and dbt packages
setup:
    uv sync
    uv run dbt deps --project-dir {{dbt_dir}}

# Acquire canonical AdventureWorks -> committed data/adventure_works/*.parquet (source-of-record)
load:
    uv run python scripts/load_adventure_works.py

# Full dbt build: seeds -> models -> tests against local DuckDB
build:
    uv run dbt build --project-dir {{dbt_dir}}

# All model tests
test:
    uv run dbt test --project-dir {{dbt_dir}}

# Source-layer tests only (challenge demo)
test-source:
    uv run dbt test --select "source:*" --project-dir {{dbt_dir}}

# Verify dbt connection/config
debug:
    uv run dbt debug --project-dir {{dbt_dir}}

# Lint everything (Python + SQL); does not modify files
lint:
    uv run ruff check .
    uv run sqlfluff lint {{dbt_dir}}/models

# Auto-format everything (Python + SQL)
fmt:
    uv run ruff check --fix .
    uv run ruff format .
    uv run sqlfluff fix {{dbt_dir}}/models

# Python type check (basic mode)
typecheck:
    uv run pyright

# Everything CI would check: lint + typecheck + build + tests
check: lint typecheck build

# Author a Conventional Commit via commitizen
commit:
    uv run cz commit

# Regenerate CHANGELOG.md from the conventional-commit history
changelog:
    uv run cz changelog

# Release: bump version from commits, update CHANGELOG.md, and create the tag
bump:
    uv run cz bump --changelog

# Remove dbt build artifacts
clean:
    uv run dbt clean --project-dir {{dbt_dir}}
