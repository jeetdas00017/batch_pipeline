import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=lambda **kwargs: None))
snowflake_module = types.ModuleType("snowflake")
connector_module = types.ModuleType("snowflake.connector")
connector_module.connect = lambda **kwargs: None
snowflake_module.connector = connector_module
sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.connector", connector_module)

from extract.repository import update_latest_timestamp


class RepositoryTests(unittest.TestCase):
    def test_update_latest_timestamp_updates_existing_run_row(self):
        conn = Mock()
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = (1,)

        with patch("extract.repository.get_sf_connection", return_value=conn):
            update_latest_timestamp("customers", "2024-01-01T00:00:00+00:00", run_id="run-001")

        self.assertTrue(cursor.execute.called)
        executed_sql = cursor.execute.call_args_list[-1].args[0]
        params = cursor.execute.call_args_list[-1].args[1]
        self.assertIn("UPDATE", executed_sql.upper())
        self.assertIn("updated_at", executed_sql.lower())
        self.assertEqual(params[0], "2024-01-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
