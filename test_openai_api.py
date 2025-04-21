import os
import sys
from dotenv import load_dotenv
from openai import OpenAI, APIError, AuthenticationError, RateLimitError, APITimeoutError

# --- Configuration ---
# Load environment variables from .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get API Key
api_key = os.getenv("OPENAI_API_KEY")

# --- Add the proxy URL --- 
PROXY_URL = "https://api.chatanywhere.tech/v1"
# --- End Proxy URL ---

# Choose a model to test 
TEST_MODEL = "gpt-3.5-turbo" # Keep gpt-3.5 for initial proxy testing
# --- End Configuration ---

def test_openai_connection():
    """Attempts a simple API call to OpenAI via proxy and prints the result."""
    print("--- OpenAI API Connection Test (via Proxy) --- ")

    # 1. Check if API Key is loaded
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please ensure it is set correctly in your .env file.")
        return
    else:
        masked_key = api_key[:5] + "..." + api_key[-4:]
        print(f"Found API Key: {masked_key}")

    # 2. Initialize OpenAI Client with Proxy Base URL
    try:
        print(f"Initializing OpenAI client with proxy: {PROXY_URL}...")
        client = OpenAI(
            api_key=api_key,
            base_url=PROXY_URL # <<< Use the defined proxy URL
        )
        print("OpenAI client initialized successfully.")
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return

    # 3. Attempt API Call via Proxy
    try:
        print(f"Attempting Chat Completion call using model: {TEST_MODEL} via proxy...")
        response = client.chat.completions.create(
            model=TEST_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Is this proxy connection working?"}
            ],
            max_tokens=50, 
            timeout=30 # Increased timeout slightly for proxy
        )
        
        print("\n--- API Call Successful (via Proxy)! ---")
        print("Response received from OpenAI via proxy.")
        if response.choices:
             print(f"Model ({TEST_MODEL}) Response: {response.choices[0].message.content}")
        else:
             print("Received response, but no choices found.")

    except AuthenticationError as e:
        print("\n--- API Call Failed: Authentication Error ---")
        print(f"Error details: {e}")
        print("Please double-check your OPENAI_API_KEY in the .env file. Ensure it's correct and active.")
    except RateLimitError as e:
        print("\n--- API Call Failed: Rate Limit Error ---")
        print(f"Error details: {e}")
        print("You may have exceeded your OpenAI API usage limits. Check your OpenAI account usage or proxy service limits.")
    except APITimeoutError as e:
        print("\n--- API Call Failed: Timeout Error ---")
        print(f"Error details: {e}")
        print("The request via the proxy timed out. Check your network connection, proxy server status, and OpenAI server status.")
    except APIError as e: 
        print("\n--- API Call Failed: OpenAI API Error (via Proxy) ---")
        print(f"Status Code: {e.status_code}")
        print(f"Error details: {e}")
        if e.code == 'model_not_found':
             print(f"The model '{TEST_MODEL}' might not exist or your key doesn't have access to it (even via proxy).")
        elif e.status_code == 404:
             print("Could not reach the proxy URL or the proxy could not reach OpenAI. Check the proxy URL and its status.")
        else:
             print("Check the error details provided.")
    except Exception as e: 
        print("\n--- API Call Failed: Unexpected Error ---")
        print(f"An unexpected error occurred: {e}")
        print("Check your network connection, proxy settings, and code.")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_openai_connection() 