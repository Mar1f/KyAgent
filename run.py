import os
import sys
import subprocess

def main():
    """Run the application"""
    print("Starting KyAgent - 考研信息查询系统")
    
    # Check if conda environment is activated
    if os.environ.get("CONDA_DEFAULT_ENV") != "py310":
        print("Warning: py310 conda environment is not activated.")
        print("It is recommended to run the application in the py310 environment.")
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != "y":
            print("Exiting...")
            sys.exit(0)
    
    # Check if MySQL is running
    try:
        # Use a simple command to check if MySQL is running
        import mysql.connector
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get database configuration
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        # Try to connect
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
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