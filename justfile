# AdventureWorks Analytics Engineering — task runner
# Prefer `just <recipe>`. Run `just` with no args to list recipes.

# dbt runs against the project-local DuckDB profile (no cloud credentials).
export DBT_PROFILES_DIR := "."

# List available recipes
default:
    @just --list

# Install Python deps (dbt + dev tools) and dbt packages
setup:
    uv sync
    uv run dbt deps

# Full dbt build: seeds -> models -> tests against local DuckDB
build:
    uv run dbt build

# All model tests
test:
    uv run dbt test

# Source-layer tests only (challenge demo)
test-source:
    uv run dbt test --select "source:*"

# Verify dbt connection/config
debug:
    uv run dbt debug

# Lint everything (Python + SQL); does not modify files
lint:
    uv run ruff check .
    uv run sqlfluff lint models

# Auto-format everything (Python + SQL)
fmt:
    uv run ruff check --fix .
    uv run ruff format .
    uv run sqlfluff fix models

# Python type check (basic mode)
typecheck:
    uv run pyright

# Everything CI would check: lint + typecheck + build + tests
check: lint typecheck build

# Author a Conventional Commit via commitizen
commit:
    uv run cz commit

# Remove dbt build artifacts
clean:
    uv run dbt clean
