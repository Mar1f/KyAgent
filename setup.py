import os
import sys
import mysql.connector
from dotenv import load_dotenv
import subprocess

# Add project root to sys.path to allow importing config and models
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

try:
    from app_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
except ImportError:
    print("Error: Could not import database configuration from app_config.py.")
    print("Ensure app_config.py exists in the project root and contains DB variables.")
    sys.exit(1)

# Load environment variables (might be redundant if app_config.py already does it, but safe)
load_dotenv()

def create_database():
    """Create MySQL database if it doesn't exist"""
    connection = None
    cursor = None
    try:
        print(f"Attempting to connect to MySQL server at {DB_HOST}:{DB_PORT}...")
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=int(DB_PORT), # Ensure port is integer
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("MySQL server connection successful.")
        
        # Create database if not exists
        cursor = connection.cursor()
        print(f"Executing: CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print(f"Database '{DB_NAME}' created or already exists.")
        return True
        
    except mysql.connector.Error as err:
        print(f"Error connecting to or creating database: {err}")
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Check your MySQL username and password in .env or app_config.py")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database doesn't exist (this shouldn't happen here)")
        else:
            print(err)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during database creation: {e}")
        return False
    finally:
        # Close connection and cursor
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection closed.")

def run_data_loader():
    """Runs the data loading script from its new location."""
    script_path = os.path.join(project_root, 'app', 'database', 'load_data.py')
    if not os.path.exists(script_path):
        print(f"Error: Data loading script not found at {script_path}")
        return False
        
    print(f"Running data loading script: {script_path}...")
    try:
        # Ensure using the correct python interpreter (could be sys.executable)
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=True, text=True)
        print("--- Data Loader Output Start ---")
        print(result.stdout)
        if result.stderr:
             print("--- Data Loader Errors/Warnings ---")
             print(result.stderr)
             print("--- End Data Loader Errors/Warnings ---")
        print("--- Data Loader Output End ---")
        print("Data loading script executed successfully.")
        return True
    except FileNotFoundError:
         print(f"Error: Could not find python interpreter '{sys.executable}' or script '{script_path}'.")
         return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing data loading script: {e}")
        print("--- Data Loader Output (Error) Start ---")
        print(e.stdout)
        print(e.stderr)
        print("--- Data Loader Output (Error) End ---")
        return False
    except Exception as e:
         print(f"An unexpected error occurred while running the data loader: {e}")
         return False

def main():
    print("--- KyAgent Setup Start ---")
    
    # 1. Create database if it doesn't exist
    print("\nStep 1: Checking/Creating Database...")
    if not create_database():
        print("\nStep 1 Failed: Could not create or verify database. Exiting setup.")
        sys.exit(1)
    print("Step 1 Complete: Database checked/created.")
    
    # 2. Run the data loading script (which also handles table creation)
    print("\nStep 2: Loading data from Excel files...")
    if not run_data_loader():
        print("\nStep 2 Failed: Data loading process encountered errors. Check logs above.")
        # Decide if you want to exit or continue
        # sys.exit(1) 
    else:
        print("Step 2 Complete: Data loading finished.")
    
    print("\n--- KyAgent Setup Finished ---")
    print("Setup process completed. Please check the logs above for any warnings or errors.")
    print("You can now try running the application with: python run.py")

if __name__ == "__main__":
    main() 