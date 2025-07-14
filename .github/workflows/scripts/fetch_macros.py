import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore
from config import PROJECT_NAME

def initialize_firebase():
    """Initialize Firebase Admin SDK using service account JSON from environment variable."""
    try:
        # Get the service account JSON from environment variable
        service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        
        if not service_account_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set")
        
        # Parse the JSON string into a dictionary
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {str(e)}")
        
        # Initialize Firebase Admin with the service account info
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        
        print("Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

def fetch_macros():
    """Fetch macro configuration values from Firestore."""
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Get reference to macros document using the global project name
        doc_ref = db.collection(PROJECT_NAME).document('macros').collection('settings').document('macros')
        doc = doc_ref.get()
        
        if not doc.exists:
            print("No macros document found in Firestore")
            return None
        
        macros_data = doc.to_dict()
        print("Successfully fetched macros from Firestore:")
        
        # Define expected macro keys with defaults
        expected_macros = {
            'LINE_THRESHOLD': '200',
            'CHANGES_THRESHOLD': '5',
            'IMPORTANT_CHANGE_MARKERS': '#IMPORTANT-CHANGE,#IMPORTANT-CHANGES',
            'IMPORTANT_CHANGE_LABELS': 'important change,important changes'
        }
        
        # Extract values and set GitHub outputs
        for key, default_value in expected_macros.items():
            value = macros_data.get(key, default_value)
            print(f"  Key: '{key}' |  Value: {value}")
            
            # Set GitHub Actions output
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"{key.lower()}={value}\n")
        
        return macros_data
        
    except Exception as e:
        print(f"Error fetching macros: {e}")
        return None

def main():
    """Main function."""
    print("Fetching macro configuration from Firebase...")
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Fetch macros
    macros = fetch_macros()
    if macros is None:
        print("Failed to fetch macros")
        sys.exit(1)
    
    print("Macro fetch completed successfully")

if __name__ == "__main__":
    main()
