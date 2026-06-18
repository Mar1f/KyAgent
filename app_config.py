import os

DB_ENV_VARS = (
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
)

LLM_ENV_VARS = (
    "OPENAI_API_KEY",
    "MODEL",
)

SEARCH_ENV_VARS = (
    "TAVILY_API_KEY",
    "SERPER_API_KEY",
)


def get_missing_env_vars(variable_names):
    """Return the names of required environment variables that are unset."""
    return [name for name in variable_names if not os.getenv(name)]


def validate_required_env(variable_names, context="application"):
    """Raise a clear error when required environment variables are missing."""
    missing = get_missing_env_vars(variable_names)
    if missing:
        missing_names = ", ".join(missing)
        raise ValueError(f"Missing required environment variables for {context}: {missing_names}")


# Database Configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Construct the database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

OPENAI_API_URL = os.getenv("OPENAI_API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
