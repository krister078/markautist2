import os
import json
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import base64
import logging
from fetch_macros import initialize_firebase, fetch_macros
from config import PROJECT_NAME

class FirebaseClient:
    def __init__(self, service_account_json=None, project_name=None):
        try:
            if not firebase_admin._apps:
                # Use provided JSON string or get from environment variable
                if not service_account_json:
                    service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
                
                if not service_account_json:
                    raise ValueError("Firebase service account JSON not provided via parameter or FIREBASE_SERVICE_ACCOUNT_JSON environment variable")
                
                # Parse the JSON string into a dictionary
                try:
                    service_account_info = json.loads(service_account_json)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in Firebase service account credentials: {str(e)}")
                    
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            # Use the provided project name or fall back to the global config
            self.project_name = project_name if project_name is not None else PROJECT_NAME
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def get_architecture_summary(self, repository):
        """Get the current architecture summary for a repository"""
        if not repository:
            return None
            
        try:
            # Use project_name as the main collection path
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return data
            else:
                return None
        except Exception as e:
            logging.error(f"Error fetching architecture summary: {str(e)}")
            return None
    
    def update_architecture_summary(self, repository, summary, changes_count=0):
        """Update the architecture summary for a repository"""
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            data = {
                'repository': repository,
                'summary': summary,
                'last_updated': datetime.utcnow(),
                'changes_count': changes_count
            }
            
            doc_ref.set(data, merge=True)


        except Exception as e:
            logging.error(f"Error updating architecture summary: {str(e)}")
            raise
    
    def add_architecture_change(self, repository, pr_number, diff, metadata=None):
        """Add a new architecture change record"""
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_changes').collection('changes').document()
            change_data = {
                'repository': repository,
                'pr_number': pr_number,
                'diff': diff,
                'timestamp': datetime.utcnow(),
                'metadata': metadata or {}
            }
            doc_ref.set(change_data)
            return doc_ref.id
        except Exception as e:
            logging.error(f"Error adding architecture change: {str(e)}")
            raise
    
    def get_recent_changes(self, repository, limit=10):
        """Get recent architecture changes for context"""
        try:
            query = (self.db.collection(self.project_name).document('architecture_changes').collection('changes')
                    .where(filter=firestore.FieldFilter('repository', '==', repository))
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            changes = []
            for doc in query.stream():
                data = doc.to_dict()
                changes.append(data)
            
            return changes
        except Exception as e:
            logging.error(f"Error getting recent changes: {str(e)}")
            return []
    
    def should_summarize(self, repository, changes_threshold=None):
        """Determine if we should regenerate the architecture summary"""
        if changes_threshold is None:
            # Get from Firebase macros or environment variable
            changes_threshold = self.get_changes_threshold()
            
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            doc = doc_ref.get()
            
            if not doc.exists:
                return True
            
            data = doc.to_dict()
            changes_count = data.get('changes_count', 0)
            should_summarize = changes_count >= changes_threshold
            return should_summarize
        except Exception as e:
            logging.error(f"Error checking should_summarize: {str(e)}")
            return False
    
    def get_changes_threshold(self):
        """Get the changes threshold from Firebase macros or environment variable"""
        try:
            # First try to get from Firebase using the imported fetch_macros function
            macros = fetch_macros()
            
            if macros and 'CHANGES_THRESHOLD' in macros:
                threshold = macros['CHANGES_THRESHOLD']
                return int(threshold)
            
            # Fallback to environment variable
            env_threshold = os.environ.get('CHANGES_THRESHOLD')
            if env_threshold is not None:
                return int(env_threshold)
            
            # Default fallback
            # Fallback to default threshold
            return 5
            
        except (ValueError, TypeError) as e:
            logging.error(f"Error parsing CHANGES_THRESHOLD: {str(e)}")
            return 5
