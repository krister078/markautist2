#!/usr/bin/env python3
"""
Debug Firebase operations script
"""
import os
import sys
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_firebase_operations():
    """Debug Firebase operations with detailed logging"""
    print("=== Firebase Debug Information ===")
    
    # Environment check
    print("\n1. Environment Variables:")
    firebase_env = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    print(f"   FIREBASE_SERVICE_ACCOUNT_JSON present: {firebase_env is not None}")
    if firebase_env:
        print(f"   Length: {len(firebase_env)} characters")
        try:
            parsed = json.loads(firebase_env)
            print(f"   Valid JSON: Yes")
            print(f"   Project ID: {parsed.get('project_id', 'NOT FOUND')}")
            print(f"   Client Email: {parsed.get('client_email', 'NOT FOUND')}")
            print(f"   Has private_key: {('private_key' in parsed)}")
        except json.JSONDecodeError as e:
            print(f"   Valid JSON: No - {e}")
    
    # Firebase imports
    print("\n2. Firebase Imports:")
    try:
        import firebase_admin
        print("   firebase_admin: OK")
        from firebase_admin import credentials, firestore
        print("   credentials and firestore: OK")
    except ImportError as e:
        print(f"   Import error: {e}")
        return False
    
    # Firebase initialization
    print("\n3. Firebase Initialization:")
    try:
        if firebase_admin._apps:
            print("   Already initialized")
        else:
            service_account_info = json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"))
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("   Initialization: OK")
    except Exception as e:
        print(f"   Initialization error: {e}")
        return False
    
    # Firestore client
    print("\n4. Firestore Client:")
    try:
        db = firestore.client()
        print("   Client creation: OK")
    except Exception as e:
        print(f"   Client creation error: {e}")
        return False
    
    # Test operations
    print("\n5. Test Operations:")
    
    # Test 1: List collections
    try:
        print("   Testing collection listing...")
        start_time = time.time()
        collections = list(db.collections())
        elapsed = time.time() - start_time
        print(f"   Collections found: {len(collections)} in {elapsed:.2f}s")
        for col in collections:
            print(f"      - {col.id}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   Collection listing failed after {elapsed:.2f}s: {e}")
    
    # Test 2: Read macros document
    try:
        print("   Testing macros document read...")
        start_time = time.time()
        doc_ref = db.collection('macros').document('macros')
        doc = doc_ref.get()
        elapsed = time.time() - start_time
        print(f"   Macros document read in {elapsed:.2f}s")
        print(f"   Document exists: {doc.exists}")
        if doc.exists:
            data = doc.to_dict()
            print(f"   Document keys: {list(data.keys()) if data else 'None'}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   Macros document read failed after {elapsed:.2f}s: {e}")
    
    # Test 3: Test document operations
    try:
        print("   Testing test document operations...")
        start_time = time.time()
        test_ref = db.collection('test').document('debug')
        
        # Write test
        test_ref.set({'timestamp': time.time(), 'test': 'debug'})
        write_time = time.time() - start_time
        print(f"   Test write completed in {write_time:.2f}s")
        
        # Read test
        read_start = time.time()
        test_doc = test_ref.get()
        read_time = time.time() - read_start
        print(f"   Test read completed in {read_time:.2f}s")
        print(f"   Test document exists: {test_doc.exists}")
        
        # Clean up
        test_ref.delete()
        print("   Test document cleaned up")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   Test document operations failed after {elapsed:.2f}s: {e}")
    
    print("\n=== Debug Complete ===")
    return True

if __name__ == "__main__":
    try:
        debug_firebase_operations()
    except Exception as e:
        print(f"Debug script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
