import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path


class ConfigEnvLoadingTests(unittest.TestCase):
    def test_reads_pg_values_from_dotenv_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dotenv_path = Path(tmp_dir) / ".env"
            dotenv_path.write_text(
                "PG_SOURCE_SCHEMA=postgres_table\nPG_TIMESTAMP_COLUMN=updated_at\n",
                encoding="utf-8",
            )

            old_cwd = os.getcwd()
            os.chdir(tmp_dir)
            sys.modules.pop("extract.utils.config", None)
            try:
                module = importlib.import_module("extract.utils.config")
            finally:
                os.chdir(old_cwd)
                sys.modules.pop("extract.utils.config", None)

            self.assertEqual(module.SOURCE_SCHEMA, "postgres_table")
            self.assertEqual(module.TIMESTAMP_COLUMN, "updated_at")

    def test_defaults_when_pg_env_missing(self) -> None:
        old_cwd = os.getcwd()
        os.chdir(tempfile.mkdtemp())
        sys.modules.pop("extract.utils.config", None)
        try:
            module = importlib.import_module("extract.utils.config")
        finally:
            os.chdir(old_cwd)
            sys.modules.pop("extract.utils.config", None)

        self.assertEqual(module.SOURCE_SCHEMA, "postgres_table")
        self.assertEqual(module.TIMESTAMP_COLUMN, "updated_at")


if __name__ == "__main__":
    unittest.main()
