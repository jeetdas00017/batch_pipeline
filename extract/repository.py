from datetime import datetime, timezone

from extract.utils.config import (
    CONTROL_SCHEMA,
    CONTROL_TABLE_PLACEHOLDER_DATE,
    CONTROL_TABLE_WATERMARK_COLUMN,
    control_table_name,
)
from extract.utils.db_utils import get_sf_connection
from extract.utils.logging_config import logger


def get_latest_timestamp(table_name: str) -> str:
    logger.info("Fetching latest timestamp for table=%s", table_name)
    conn = get_sf_connection(schema=CONTROL_SCHEMA)

    try:
        query = (
            f"SELECT MAX({CONTROL_TABLE_WATERMARK_COLUMN}) AS latest_timestamp "
            f"FROM {control_table_name()} "
            f"WHERE table_name = %s"
        )
        cur = conn.cursor()
        cur.execute(query, (table_name,))
        result = cur.fetchone()
        latest_timestamp = str(result[0]) if result and result[0] is not None else CONTROL_TABLE_PLACEHOLDER_DATE

        logger.info("Latest timestamp for %s: %s", table_name, latest_timestamp)
        return latest_timestamp
    finally:
        conn.close()


def update_latest_timestamp(table_name: str, latest_timestamp_value: str, run_id: str | None = None):
    logger.info("Updating latest timestamp for table=%s", table_name)
    conn = get_sf_connection(schema=CONTROL_SCHEMA)

    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)

        if run_id is not None:
            cur.execute(
                f"SELECT 1 FROM {control_table_name()} WHERE table_name = %s AND run_id = %s",
                (table_name, run_id),
            )
            existing_row = cur.fetchone()
            if existing_row is not None:
                cur.execute(
                    f"UPDATE {control_table_name()} SET {CONTROL_TABLE_WATERMARK_COLUMN} = %s, updated_at = %s WHERE table_name = %s AND run_id = %s",
                    (latest_timestamp_value, now, table_name, run_id),
                )
            else:
                cur.execute(
                    f"INSERT INTO {control_table_name()} (run_id, table_name, status, rows_processed, new_rows, existing_rows_updated, started_at, completed_at, updated_at, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (run_id, table_name, "success", 0, 0, 0, now, now, now, "Watermark updated"),
                )
        else:
            cur.execute(
                f"SELECT 1 FROM {control_table_name()} WHERE table_name = %s ORDER BY updated_at DESC LIMIT 1",
                (table_name,),
            )
            existing_row = cur.fetchone()
            if existing_row is not None:
                cur.execute(
                    f"UPDATE {control_table_name()} SET {CONTROL_TABLE_WATERMARK_COLUMN} = %s, updated_at = %s WHERE table_name = %s",
                    (latest_timestamp_value, now, table_name),
                )
            else:
                cur.execute(
                    f"INSERT INTO {control_table_name()} (table_name, {CONTROL_TABLE_WATERMARK_COLUMN}, updated_at, status) VALUES (%s, %s, %s, %s)",
                    (table_name, latest_timestamp_value, now, "success"),
                )

        conn.commit()
        logger.info("Timestamp updated successfully for table=%s", table_name)
    finally:
        conn.close()
