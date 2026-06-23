import io
import os
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Seed minimal DB config before importing entrypoint modules.
os.environ.setdefault("DB_USER", "tester")
os.environ.setdefault("DB_PASSWORD", "secret")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "kyagent_test")

import run
import setup
import test_openai_api


class RunEntrypointTests(unittest.TestCase):
    @patch("run.subprocess.run")
    @patch("run.input", return_value="y")
    @patch("mysql.connector.connect")
    @patch("app_config.validate_required_env")
    def test_main_starts_streamlit_when_checks_pass(self, mock_validate, mock_connect, mock_input, mock_subprocess):
        connection = MagicMock()
        mock_connect.return_value = connection

        with patch.dict(os.environ, {"DB_HOST": "localhost", "DB_PORT": "3306", "DB_USER": "tester", "DB_PASSWORD": "secret", "VIRTUAL_ENV": "/tmp/venv"}, clear=False):
            run.main()

        mock_validate.assert_called_once()
        mock_connect.assert_called_once()
        connection.close.assert_called_once()
        mock_subprocess.assert_called_once_with(["streamlit", "run", "app/app.py"])

    @patch("run.subprocess.run")
    @patch("run.input", return_value="n")
    @patch("app_config.validate_required_env", side_effect=ValueError("missing DB config"))
    def test_main_exits_when_db_config_invalid(self, mock_validate, mock_input, mock_subprocess):
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/tmp/venv"}, clear=False):
            with self.assertRaises(SystemExit) as ctx:
                run.main()

        self.assertEqual(ctx.exception.code, 1)
        mock_validate.assert_called_once()
        mock_subprocess.assert_not_called()


class SetupEntrypointTests(unittest.TestCase):
    @patch("setup.validate_required_env")
    @patch("setup.mysql.connector.connect")
    def test_create_database_executes_create_statement(self, mock_connect, mock_validate):
        cursor = MagicMock()
        connection = MagicMock()
        connection.cursor.return_value = cursor
        connection.is_connected.return_value = True
        mock_connect.return_value = connection

        result = setup.create_database()

        self.assertTrue(result)
        mock_validate.assert_called_once()
        cursor.execute.assert_called_once()
        self.assertIn("CREATE DATABASE IF NOT EXISTS", cursor.execute.call_args[0][0])
        connection.close.assert_called_once()

    def test_run_data_loader_returns_false_when_script_missing(self):
        with patch("setup.os.path.exists", return_value=False):
            self.assertFalse(setup.run_data_loader())

    @patch("setup.subprocess.run")
    def test_run_data_loader_returns_true_on_success(self, mock_run):
        mock_run.return_value = SimpleNamespace(stdout="ok", stderr="")
        with patch("setup.os.path.exists", return_value=True):
            self.assertTrue(setup.run_data_loader())


class TestOpenAIEntrypointTests(unittest.TestCase):
    def test_connection_test_reports_configuration_error_early(self):
        with patch("test_openai_api.validate_required_env", side_effect=ValueError("missing llm config")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                test_openai_api.test_openai_connection()

        output = buf.getvalue()
        self.assertIn("Configuration error", output)
        self.assertIn("missing llm config", output)


if __name__ == "__main__":
    unittest.main()
