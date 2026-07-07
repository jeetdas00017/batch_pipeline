import sys
import types
import unittest
from unittest.mock import Mock, patch

fake_module = types.ModuleType("faker")
fake_module.Faker = lambda: None
sys.modules.setdefault("faker", fake_module)

psycopg2_module = types.ModuleType("psycopg2")
psycopg2_module.connect = lambda **kwargs: None
sys.modules.setdefault("psycopg2", psycopg2_module)

psycopg2_extras_module = types.ModuleType("psycopg2.extras")
psycopg2_extras_module.execute_values = lambda cursor, query, rows: None
sys.modules.setdefault("psycopg2.extras", psycopg2_extras_module)

from extract.insert.insert_to_postgres import get_next_id


class InsertToPostgresTests(unittest.TestCase):
    def test_get_next_id_uses_configured_schema(self):
        cursor = Mock()
        cursor.fetchone.return_value = (5,)

        with patch("extract.insert.insert_to_postgres.SOURCE_SCHEMA", "postgres_table"):
            result = get_next_id(cursor, "customers", "customer_id")

        self.assertEqual(result, 5)
        executed_query = cursor.execute.call_args[0][0]
        self.assertIn("FROM postgres_table.customers", executed_query)


if __name__ == "__main__":
    unittest.main()
