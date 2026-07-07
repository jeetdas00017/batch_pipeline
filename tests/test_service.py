import os
import sys
import types
import unittest
from datetime import datetime

os.environ.setdefault("PG_DATABASE", "testdb")
os.environ.setdefault("PG_USER", "testuser")
os.environ.setdefault("PG_PASSWORD", "testpass")
os.environ.setdefault("SF_ACCOUNT", "testaccount")
os.environ.setdefault("SF_USER", "testuser")
os.environ.setdefault("SF_PASSWORD", "testpass")
os.environ.setdefault("SF_DATABASE", "testdb")
os.environ.setdefault("SF_WAREHOUSE", "testwh")
os.environ.setdefault("SF_ROLE", "testrole")
os.environ.setdefault("S3_RAW_BUCKET", "testbucket")

pandas_module = types.ModuleType("pandas")
pandas_module.DataFrame = object
sys.modules.setdefault("pandas", pandas_module)

dotenv_module = types.ModuleType("dotenv")
dotenv_module.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_module)

pyarrow_module = types.ModuleType("pyarrow")
pyarrow_parquet_module = types.ModuleType("pyarrow.parquet")
pyarrow_parquet_module.ParquetWriter = object
pyarrow_module.parquet = pyarrow_parquet_module
sys.modules.setdefault("pyarrow", pyarrow_module)
sys.modules.setdefault("pyarrow.parquet", pyarrow_parquet_module)

boto3_module = types.ModuleType("boto3")
boto3_module.client = lambda *args, **kwargs: None
sys.modules.setdefault("boto3", boto3_module)

botocore_module = types.ModuleType("botocore")
botocore_config_module = types.ModuleType("botocore.config")
botocore_config_module.Config = object
botocore_module.config = botocore_config_module
sys.modules.setdefault("botocore", botocore_module)
sys.modules.setdefault("botocore.config", botocore_config_module)

sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=lambda **kwargs: None))
snowflake_module = types.ModuleType("snowflake")
connector_module = types.ModuleType("snowflake.connector")
connector_module.connect = lambda **kwargs: None
snowflake_module.connector = connector_module
sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.connector", connector_module)

from extract import service


class ServiceTests(unittest.TestCase):
    def test_format_timestamp_for_log_converts_to_ist_iso(self):
        value = datetime(2026, 7, 7, 20, 14, 27, 776453)

        formatted = service._format_timestamp_for_log(value)

        self.assertEqual(formatted, "2026-07-08T01:44:27.776453+05:30")


if __name__ == "__main__":
    unittest.main()
