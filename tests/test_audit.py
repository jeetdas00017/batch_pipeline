import sys
import types
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=lambda **kwargs: None))
snowflake_module = types.ModuleType("snowflake")
connector_module = types.ModuleType("snowflake.connector")
connector_module.connect = lambda **kwargs: None
snowflake_module.connector = connector_module
sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.connector", connector_module)

from extract.audit import insert_audit_entry


class AuditTests(unittest.TestCase):
    def test_insert_audit_entry_uses_matching_parameter_count(self):
        conn = Mock()
        cursor = conn.cursor.return_value

        with patch("extract.audit.get_sf_connection", return_value=conn):
            insert_audit_entry("run-001", "customers", "running", notes="Extraction started")

        self.assertTrue(cursor.execute.called)
        _, params = cursor.execute.call_args.args
        self.assertEqual(len(params), 10)

    def test_insert_audit_entry_uses_ist_timezone(self):
        conn = Mock()
        cursor = conn.cursor.return_value

        with patch("extract.audit.get_sf_connection", return_value=conn):
            insert_audit_entry("run-001", "customers", "running", notes="Extraction started")

        self.assertTrue(cursor.execute.called)
        _, params = cursor.execute.call_args.args
        started_at = params[6]
        updated_at = params[8]
        self.assertEqual(started_at.tzinfo, ZoneInfo("Asia/Kolkata"))
        self.assertEqual(updated_at.tzinfo, ZoneInfo("Asia/Kolkata"))


if __name__ == "__main__":
    unittest.main()
