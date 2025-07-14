import os
import json
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import logging
from config import PROJECT_NAME

class DockerImageManager:
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
    
    def get_stored_digest(self, image_name):
        """Get the stored Docker image digest for a given image"""
        try:
            # Convert image name to document ID (replace special characters)
            doc_id = image_name.replace('/', '_').replace(':', '_')
            
            doc_ref = self.db.collection(self.project_name).document('docker_images').collection('digests').document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                stored_digest = data.get('digest', '')
                last_updated = data.get('last_updated')
                
                if stored_digest:
                    print(f"Found stored digest for {image_name}: {stored_digest}", file=sys.stderr)
                    if last_updated:
                        print(f"Last updated: {last_updated}", file=sys.stderr)
                    return stored_digest
                else:
                    print(f"Document exists for {image_name} but digest is empty", file=sys.stderr)
                    return ""
            else:
                print(f"No stored digest found for {image_name} - this appears to be the first run", file=sys.stderr)
                return ""
                
        except Exception as e:
            print(f"Error fetching stored digest for {image_name}: {str(e)}", file=sys.stderr)
            print("This might be the first run or a connection issue", file=sys.stderr)
            return ""
    
    def update_digest(self, image_name, digest, tag="latest", repository=None, updated_by=None):
        """Update the stored Docker image digest"""
        try:
            # Convert image name to document ID (replace special characters)
            doc_id = image_name.replace('/', '_').replace(':', '_')
            
            doc_ref = self.db.collection(self.project_name).document('docker_images').collection('digests').document(doc_id)
            
            data = {
                'digest': digest,
                'image_name': image_name,
                'tag': tag,
                'last_updated': datetime.utcnow(),
                'repository': repository or os.environ.get('GITHUB_REPOSITORY', ''),
                'updated_by': updated_by or 'monitor-agent-updates-workflow'
            }
            
            doc_ref.set(data, merge=True)
            print(f"Successfully updated digest for {image_name} in project {self.project_name}", file=sys.stderr)
            print(f"New digest: {digest}", file=sys.stderr)
            return True
            
        except Exception as e:
            logging.error(f"Error updating digest for {image_name}: {str(e)}")
            raise
    
    def get_digest_history(self, image_name, limit=10):
        """Get recent digest update history for an image (if we implement versioning later)"""
        try:
            # For now, just return the current digest info
            doc_id = image_name.replace('/', '_').replace(':', '_')
            doc_ref = self.db.collection(self.project_name).document('docker_images').collection('digests').document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return [doc.to_dict()]
            else:
                return []
                
        except Exception as e:
            logging.error(f"Error getting digest history for {image_name}: {str(e)}")
            return []
    
    def list_tracked_images(self):
        """List all Docker images being tracked"""
        try:
            collection_ref = self.db.collection(self.project_name).document('docker_images').collection('digests')
            docs = collection_ref.stream()
            
            images = []
            for doc in docs:
                data = doc.to_dict()
                images.append({
                    'doc_id': doc.id,
                    'image_name': data.get('image_name', ''),
                    'digest': data.get('digest', ''),
                    'tag': data.get('tag', ''),
                    'last_updated': data.get('last_updated'),
                    'repository': data.get('repository', ''),
                    'updated_by': data.get('updated_by', '')
                })
            
            print(f"Found {len(images)} tracked images in project {self.project_name}", file=sys.stderr)
            return images
            
        except Exception as e:
            logging.error(f"Error listing tracked images: {str(e)}")
            return []

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python docker_image_manager.py <command> [args...]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  get_digest <image_name>", file=sys.stderr)
        print("  update_digest <image_name> <digest> [tag] [repository] [updated_by]", file=sys.stderr)
        print("  list_images", file=sys.stderr)
        sys.exit(1)
    
    try:
        manager = DockerImageManager()
        command = sys.argv[1]
        
        if command == "get_digest":
            if len(sys.argv) < 3:
                print("Error: image_name required", file=sys.stderr)
                sys.exit(1)
            
            image_name = sys.argv[2]
            digest = manager.get_stored_digest(image_name)
            
            if digest:
                print(f"stored_digest={digest}")
            else:
                print("stored_digest=")
        
        elif command == "update_digest":
            if len(sys.argv) < 4:
                print("Error: image_name and digest required", file=sys.stderr)
                sys.exit(1)
            
            image_name = sys.argv[2]
            digest = sys.argv[3]
            tag = sys.argv[4] if len(sys.argv) > 4 else "latest"
            repository = sys.argv[5] if len(sys.argv) > 5 else None
            updated_by = sys.argv[6] if len(sys.argv) > 6 else None
            
            manager.update_digest(image_name, digest, tag, repository, updated_by)
            print("Digest updated successfully")
        
        elif command == "list_images":
            images = manager.list_tracked_images()
            for img in images:
                print(f"Image: {img['image_name']}, Digest: {img['digest'][:12]}..., Updated: {img['last_updated']}")
        
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
