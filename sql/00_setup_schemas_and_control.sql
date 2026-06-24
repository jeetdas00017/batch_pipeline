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

-- Seed placeholder rows so the first run starts from the configured fallback date.
INSERT INTO etl_control.extract_audit_log (table_name, last_extracted_at, updated_at, status)
SELECT t.table_name, '1900-01-01 00:00:00'::timestamp, CURRENT_TIMESTAMP(), 'success'
FROM (VALUES ('customers'), ('products'), ('orders')) AS t(table_name)
WHERE NOT EXISTS (
    SELECT 1 FROM etl_control.extract_audit_log a WHERE a.table_name = t.table_name
);
