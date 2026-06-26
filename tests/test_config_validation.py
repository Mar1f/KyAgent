import os
import unittest
from unittest.mock import patch

# Seed minimal DB config before importing modules that construct DATABASE_URL.
os.environ.setdefault("DB_USER", "tester")
os.environ.setdefault("DB_PASSWORD", "secret")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "kyagent_test")

from app_config import validate_required_env
from app.api.langchain_setup import LangChainManager


class ValidateRequiredEnvTests(unittest.TestCase):
    def test_validate_required_env_passes_when_values_exist(self):
        with patch.dict(os.environ, {"ALPHA": "1", "BETA": "2"}, clear=False):
            validate_required_env(("ALPHA", "BETA"), context="unit-test")

    def test_validate_required_env_raises_with_missing_names(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                validate_required_env(("ALPHA", "BETA"), context="unit-test")

        self.assertIn("unit-test", str(ctx.exception))
        self.assertIn("ALPHA", str(ctx.exception))
        self.assertIn("BETA", str(ctx.exception))


class LangChainManagerValidationTests(unittest.TestCase):
    @patch("app.api.langchain_setup.ChatOpenAI")
    @patch("app.api.langchain_setup.SQLDatabaseToolkit")
    @patch("app.api.langchain_setup.SQLDatabase")
    @patch("app.api.langchain_setup.create_engine")
    @patch("app.api.langchain_setup.GoogleSerperAPIWrapper")
    @patch("app.api.langchain_setup.TavilySearchResults", side_effect=RuntimeError("tavily down"))
    @patch.object(LangChainManager, "setup_agent")
    def test_langchain_manager_falls_back_to_dummy_tavily_tool(self, mock_setup_agent, mock_tavily, mock_serper, mock_create_engine, mock_sql_db, mock_sql_toolkit, mock_chat_openai):
        env = {
            "DB_USER": "tester",
            "DB_PASSWORD": "secret",
            "DB_HOST": "localhost",
            "DB_PORT": "3306",
            "DB_NAME": "kyagent_test",
            "OPENAI_API_KEY": "openai-key",
            "MODEL": "gpt-4o-mini",
            "TAVILY_API_KEY": "tavily-key",
            "SERPER_API_KEY": "serper-key",
        }
        mock_sql_toolkit.return_value.get_tools.return_value = []
        with patch.dict(os.environ, env, clear=True):
            manager = LangChainManager()

        self.assertEqual(manager.search_tools[0].name, "Google Search")
        self.assertEqual(manager.search_tools[1].name, "Tavily Search")
        self.assertEqual(manager.search_tools[1].func("query"), "Tavily Search tool initialization failed.")
        mock_setup_agent.assert_called_once()

    def test_langchain_manager_requires_llm_env(self):
        env = {
            "DB_USER": "tester",
            "DB_PASSWORD": "secret",
            "DB_HOST": "localhost",
            "DB_PORT": "3306",
            "DB_NAME": "kyagent_test",
            "TAVILY_API_KEY": "tavily-key",
            "SERPER_API_KEY": "serper-key",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError) as ctx:
                LangChainManager()

        self.assertIn("LangChainManager LLM setup", str(ctx.exception))
        self.assertIn("OPENAI_API_KEY", str(ctx.exception))
        self.assertIn("MODEL", str(ctx.exception))

    def test_langchain_manager_requires_search_env(self):
        env = {
            "DB_USER": "tester",
            "DB_PASSWORD": "secret",
            "DB_HOST": "localhost",
            "DB_PORT": "3306",
            "DB_NAME": "kyagent_test",
            "OPENAI_API_KEY": "openai-key",
            "MODEL": "gpt-4o-mini",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError) as ctx:
                LangChainManager()

        self.assertIn("LangChainManager search setup", str(ctx.exception))
        self.assertIn("TAVILY_API_KEY", str(ctx.exception))
        self.assertIn("SERPER_API_KEY", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
