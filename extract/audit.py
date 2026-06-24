from datetime import datetime, timezone

from extract.utils.config import CONTROL_SCHEMA, CONTROL_TABLE
from extract.utils.db_utils import get_sf_connection
from extract.utils.logging_config import logger


def ensure_audit_table() -> None:
    conn = get_sf_connection(schema=CONTROL_SCHEMA)
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CONTROL_SCHEMA}.{CONTROL_TABLE} (
                run_id VARCHAR(255),
                table_name VARCHAR(100),
                status VARCHAR(20),
                rows_processed NUMBER,
                new_rows NUMBER,
                existing_rows_updated NUMBER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                updated_at TIMESTAMP,
                notes VARCHAR(4000)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_audit_entry(run_id: str, table_name: str, status: str, rows_processed: int = 0,
                       new_rows: int = 0, existing_rows_updated: int = 0,
                       notes: str | None = None) -> None:
    conn = get_sf_connection(schema=CONTROL_SCHEMA)
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)
        cur.execute(
            f"""
            INSERT INTO {CONTROL_SCHEMA}.{CONTROL_TABLE} (
                run_id, table_name, status, rows_processed, new_rows,
                existing_rows_updated, started_at, completed_at, updated_at, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                table_name,
                status,
                rows_processed,
                new_rows,
                existing_rows_updated,
                now,
                None,
                now,
                notes,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_audit_entry(run_id: str, table_name: str, status: str, rows_processed: int | None = None,
                       new_rows: int | None = None, existing_rows_updated: int | None = None,
                       notes: str | None = None) -> None:
    conn = get_sf_connection(schema=CONTROL_SCHEMA)
    try:
        cur = conn.cursor()
        set_parts = ["status = %s", "updated_at = %s"]
        values: list[object] = [status, datetime.now(timezone.utc)]

        if rows_processed is not None:
            set_parts.append("rows_processed = %s")
            values.append(rows_processed)
        if new_rows is not None:
            set_parts.append("new_rows = %s")
            values.append(new_rows)
        if existing_rows_updated is not None:
            set_parts.append("existing_rows_updated = %s")
            values.append(existing_rows_updated)
        if notes is not None:
            set_parts.append("notes = %s")
            values.append(notes)

        values.extend([run_id, table_name])
        cur.execute(
            f"UPDATE {CONTROL_SCHEMA}.{CONTROL_TABLE} SET {', '.join(set_parts)} "
            f"WHERE run_id = %s AND table_name = %s",
            tuple(values),
        )
        conn.commit()
    finally:
        conn.close()
