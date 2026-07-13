# Superset image + the DuckDB SQLAlchemy driver (ADR-0002: Superset reads the DuckDB marts
# directly, no separate warehouse). Base image pinned for reproducibility.
FROM apache/superset:4.1.1

USER root
RUN pip install --no-cache-dir duckdb==1.1.3 duckdb-engine==0.13.6
USER superset
