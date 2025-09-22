# authenticate.py
import os
from google_tasks import GoogleTasks

def main():
    """Authenticates with Google Tasks and creates token.json."""
    if os.path.exists('token.json'):
        print("token.json already exists. Authentication may not be needed.")
    else:
        print("Starting authentication process...")
        # Instantiating the class will trigger the authentication method
        GoogleTasks()

if __name__ == "__main__":
    main()