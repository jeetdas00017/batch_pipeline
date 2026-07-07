import os
from datetime import datetime, timedelta, timezone
import time

import pandas as pd

from extract.utils.config import TABLE_CONFIG, SOURCE_SCHEMA, TIMESTAMP_COLUMN, build_s3_key, S3_BUCKET, RAW_SCHEMA
from extract.utils.db_utils import get_pg_connection, get_sf_connection
from extract.utils.parquet_utils import write_dataframe_to_parquet
from extract.repository import get_latest_timestamp, update_latest_timestamp
from extract.utils.s3_utils import upload_file_to_s3
from extract.utils.logging_config import logger
from extract.audit import insert_audit_entry, update_audit_entry

IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
UTC_TIMEZONE = timezone.utc


def _normalize_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if getattr(value, "tzinfo", None) is None:
        value = value.replace(tzinfo=UTC_TIMEZONE)

    return value.astimezone(IST_TIMEZONE)


def _format_timestamp_for_log(value: datetime | None) -> str | None:
    normalized = _normalize_timestamp(value)
    if normalized is None:
        return None

    return normalized.isoformat()


def _format_timestamp_map_for_log(values: dict) -> dict:
    return {
        table_name: _format_timestamp_for_log(value)
        for table_name, value in values.items()
    }


def _build_extract_query(table_name: str) -> str:
    return (
        f"SELECT * FROM {SOURCE_SCHEMA}.{table_name} "
        f"WHERE {TIMESTAMP_COLUMN} > %s "
        f"ORDER BY {TIMESTAMP_COLUMN} DESC"
    )


def _read_table(table_name: str, latest_timestamp: str) -> pd.DataFrame:
    query = _build_extract_query(table_name)
    logger.info("Reading table %s with latest_timestamp=%s", table_name, latest_timestamp)
    parsed_timestamp = _normalize_timestamp(
        datetime.fromisoformat(latest_timestamp.replace("Z", "+00:00"))
    ) if latest_timestamp else None
    with get_pg_connection() as pg_conn:
        df = pd.read_sql(query, pg_conn, params=(parsed_timestamp,))
    return df


def _write_extract_output(table_name: str, df: pd.DataFrame, execution_date: str, run_ts: str) -> dict:
    local_path = os.path.join("/tmp", f"{table_name}_{run_ts}.parquet")

    write_dataframe_to_parquet(df, local_path)
    s3_key = build_s3_key(table_name, execution_date, run_ts)
    upload_file_to_s3(local_path, S3_BUCKET, s3_key)
    os.remove(local_path)
    return {"table": table_name, "rows": len(df), "s3_key": s3_key}

def wait_for_max_time_sync(**context):
    """Wait until PostgreSQL and Snowflake raw tables have matching max timestamps."""
    tables = [table_name.lower() for table_name in TABLE_CONFIG]
    snowflake_schema = RAW_SCHEMA
    max_attempts = 10
    sleep_seconds = 60

    for attempt in range(1, max_attempts + 1):
        pg_max_timestamp = {}
        sf_max_timestamp = {}

        with get_pg_connection() as pg_conn:
            with pg_conn.cursor() as pg_cursor:
                for table_name in tables:
                    pg_cursor.execute(f"SELECT max(updated_at) FROM {SOURCE_SCHEMA}.{table_name}")
                    pg_max_timestamp[table_name] = pg_cursor.fetchone()[0]

        with get_sf_connection(schema=RAW_SCHEMA) as sf_conn:
            with sf_conn.cursor() as sf_cursor:
                for table_name in tables:
                    sf_cursor.execute(f"SELECT max(updated_at) FROM {snowflake_schema}.{table_name.upper()}")
                    sf_max_timestamp[table_name] = sf_cursor.fetchone()[0]

        logger.info(
            "Max timestamp check attempt %s: postgres=%s, snowflake=%s",
            attempt,
            _format_timestamp_map_for_log(pg_max_timestamp),
            _format_timestamp_map_for_log(sf_max_timestamp),
        )

        if pg_max_timestamp == sf_max_timestamp:
            logger.info("Max timestamps are synchronized for all configured tables.")
            return True

        if attempt < max_attempts:
            logger.info("Max timestamps are not yet aligned. Waiting %s seconds before retrying.", sleep_seconds)
            time.sleep(sleep_seconds)

    raise AirflowException(
        f"Timed out waiting for max timestamps to match for tables: {', '.join(tables)}"
    )

def extract_table(table_name: str, execution_date: str, run_ts: str, run_id: str | None = None) -> dict:
    run_id = run_id or f"{execution_date}_{run_ts}_{table_name}"
    latest_timestamp = get_latest_timestamp(table_name)
    logger.info("Extracting table=%s with latest_timestamp=%s", table_name, latest_timestamp)

    insert_audit_entry(run_id, table_name, "running", notes="Extraction started")

    try:
        df = _read_table(table_name, latest_timestamp)
        logger.info("Rows extracted for %s: %s", table_name, len(df))

        if df.empty:
            logger.info("No new data for table=%s", table_name)
            update_audit_entry(run_id, table_name, "success", rows_processed=0, new_rows=0, existing_rows_updated=0, notes="No new data")
            return {"table": table_name, "rows": 0, "status": "no_data"}
        if df.empty:
            logger.info("No new data for table=%s", table_name)
            update_audit_entry(run_id, table_name, "success", rows_processed=0, new_rows=0, existing_rows_updated=0, notes="No new data")
            return {"table": table_name, "rows": 0, "status": "no_data"}

        result = _write_extract_output(table_name, df, execution_date, run_ts)
        updated_timestamp = str(df[TIMESTAMP_COLUMN].max())
        update_latest_timestamp(table_name, updated_timestamp, run_id=run_id)
        logger.info("Updated latest timestamp for table=%s to %s", table_name, updated_timestamp)
        result = _write_extract_output(table_name, df, execution_date, run_ts)
        updated_timestamp = str(df[TIMESTAMP_COLUMN].max())
        update_latest_timestamp(table_name, updated_timestamp, run_id=run_id)
        logger.info("Updated latest timestamp for table=%s to %s", table_name, updated_timestamp)

        update_audit_entry(
            run_id,
            table_name,
            "success",
            rows_processed=len(df),
            new_rows=len(df),
            existing_rows_updated=0,
            notes="Extraction completed",
        )
        return result
    except Exception as exc:
        logger.exception("Extraction failed for table=%s", table_name)
        update_audit_entry(run_id, table_name, "failed", rows_processed=0, new_rows=0, existing_rows_updated=0, notes=str(exc))
        
        


def extract_all(execution_date: str, run_ts: str) -> list[dict]:
    results = []
    for table_name in TABLE_CONFIG:
        logger.info("Starting extraction for table=%s", table_name)
        results.append(extract_table(table_name, execution_date, run_ts, run_id=f"{execution_date}_{run_ts}"))
    logger.info("Completed extraction for %s tables", len(results))
    return results
