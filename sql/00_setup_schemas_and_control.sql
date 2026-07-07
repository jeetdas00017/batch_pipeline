-- =====================================================================
-- 00_setup_schemas_and_control.sql
-- Run once during environment setup (e.g. via a one-time Airflow task
-- or a migration tool such as Flyway / sqlfluff / dbt run-operation).
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS etl_control;

-- ---------------------------------------------------------------------
-- Shared control table used by the extractor to store per-run audit rows
-- and the latest successfully extracted watermark for each source table.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etl_control.extract_audit_log (
    run_id                 VARCHAR(255),
    table_name             VARCHAR(100) NOT NULL,
    status                 VARCHAR(20),
    rows_processed         NUMBER,
    new_rows               NUMBER,
    existing_rows_updated  NUMBER,
    last_extracted_at      TIMESTAMP,
    started_at             TIMESTAMP,
    completed_at           TIMESTAMP,
    updated_at             TIMESTAMP,
    notes                  VARCHAR(4000),
    PRIMARY KEY (table_name, run_id)
);

