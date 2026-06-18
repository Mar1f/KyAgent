import os
import sys
import subprocess

from dotenv import load_dotenv


def main():
    """Run the application"""
    print("Starting KyAgent - 考研信息查询系统")

    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=dotenv_path)

    from app_config import DB_ENV_VARS, validate_required_env

    # Check if conda environment is activated
    if os.environ.get("CONDA_DEFAULT_ENV") != "py310":
        print("Warning: py310 conda environment is not activated.")
        print("It is recommended to run the application in the py310 environment.")
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != "y":
            print("Exiting...")
            sys.exit(0)

    try:
        validate_required_env(DB_ENV_VARS, context="run.py database preflight")
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)

    # Check if MySQL is running
    try:
        import mysql.connector

        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        connection.close()
        print("MySQL connection successful.")
    except Exception as e:
        print(f"Warning: Could not connect to MySQL: {str(e)}")
        print("Please make sure MySQL is running and configured correctly in .env")
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != "y":
            print("Exiting...")
            sys.exit(0)

    # Run Streamlit application
    print("Starting Streamlit application...")
    subprocess.run(["streamlit", "run", "app/app.py"])


if __name__ == "__main__":
    main()
