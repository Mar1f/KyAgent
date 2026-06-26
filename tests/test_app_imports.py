import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

# Seed minimal DB config before importing app modules.
os.environ.setdefault("DB_USER", "tester")
os.environ.setdefault("DB_PASSWORD", "secret")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "kyagent_test")
os.environ.setdefault("OPENAI_API_KEY", "openai-key")
os.environ.setdefault("MODEL", "gpt-4o-mini")
os.environ.setdefault("TAVILY_API_KEY", "tavily-key")
os.environ.setdefault("SERPER_API_KEY", "serper-key")


class AppImportTests(unittest.TestCase):
    @patch("streamlit.set_page_config")
    def test_importing_app_module_does_not_print_debug_output(self, mock_set_page_config):
        import importlib
        import sys

        sys.modules.pop("app.app", None)

        buf = io.StringIO()
        with redirect_stdout(buf):
            importlib.import_module("app.app")

        output = buf.getvalue()
        self.assertNotIn("[Debug] Added to sys.path", output)
        mock_set_page_config.assert_called_once()


if __name__ == "__main__":
    unittest.main()
