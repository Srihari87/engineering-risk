import requests
from datetime import datetime, timedelta
from src.db.connection import SessionLocal
from src.models.models import Incident, Service, File
from src.config import config
import re

class SentryConnector:
    def __init__(self):
        self.token = config.SENTRY_TOKEN
        self.org = config.SENTRY_ORG
        self.project = config.SENTRY_PROJECT
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://sentry.io/api/0"
    
    def get_issues(self, days: int = 90):
        """Fetch issues from Sentry"""
        url = f"{self.base_url}/organizations/{self.org}/issues/"
        
        # Filter by project and time range
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        params = {
            "project": self.project,
            "query": f"firstSeen:>={cutoff.isoformat()}",
            "limit": 100,
            "sort": "-firstSeen"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Error fetching issues: {response.status_code}")
                return []
            
            return response.json()
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def get_issue_events(self, issue_id: str, limit: int = 10):
        """Get events for an issue"""
        url = f"{self.base_url}/issues/{issue_id}/events/"
        
        params = {"limit": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return []
            
            return response.json()
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def extract_file_from_stacktrace(self, stacktrace: str) -> str:
        """Extract filename from stack trace"""
        if not stacktrace:
            return None
        
        # Look for file paths in stack trace
        # Pattern: "file.py" or "/path/to/file.py" or "src/file.py"
        match = re.search(r'([a-zA-Z0-9_/\-\.]+\.(?:py|ts|tsx|js|jsx|go))', stacktrace)
        
        if match:
            return match.group(1)
        
        return None
    
    def ingest_incidents(self, repo_id: int, days: int = 90):
        """Ingest incidents from Sentry"""
        db = SessionLocal()
        
        try:
            print(f"📥 Fetching incidents from Sentry...")
            
            issues = self.get_issues(days=days)
            
            if not issues:
                print("❌ No issues found")
                return 0
            
            incident_count = 0
            
            for issue in issues:
                try:
                    # Get issue details
                    issue_id = issue['id']
                    title = issue['title']
                    error_type = issue.get('type', 'Error')
                    first_seen = issue.get('firstSeen')
                    last_seen = issue.get('lastSeen')
                    event_count = issue.get('count', 0)
                    
                    # Get stack trace from latest event
                    events = self.get_issue_events(issue_id, limit=1)
                    stack_trace = ""
                    
                    if events:
                        event = events[0]
                        # Extract stack trace
                        exception = event.get('exception', {})
                        if exception and exception.get('values'):
                            stack_trace = str(exception['values'][0].get('stacktrace', {}))
                    
                    # Extract file from stack trace
                    file_path = self.extract_file_from_stacktrace(stack_trace)
                    
                    # Find service from file
                    service_id = None
                    if file_path:
                        file_obj = db.query(File).filter(
                            File.repo_id == repo_id,
                            File.path.ilike(f"%{file_path}%")
                        ).first()
                        
                        if file_obj and file_obj.service_id:
                            service_id = file_obj.service_id
                    
                    # If no service found, skip
                    if not service_id:
                        print(f"  ⚠️ {title} - no service mapping found")
                        continue
                    
                    # Check if incident already exists
                    existing = db.query(Incident).filter(
                        Incident.sentry_id == issue_id
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        existing.occurrence_count = event_count
                        db.commit()
                    else:
                        # Create new
                        incident = Incident(
                            repo_id=repo_id,
                            service_id=service_id,
                            sentry_id=issue_id,
                            title=title,
                            error_type=error_type,
                            stack_trace=stack_trace,
                            file_path=file_path,
                            first_seen=datetime.fromisoformat(first_seen.replace('Z', '+00:00')),
                            last_seen=datetime.fromisoformat(last_seen.replace('Z', '+00:00')),
                            occurrence_count=event_count,
                            is_resolved=issue.get('status') == 'resolved'
                        )
                        db.add(incident)
                        db.commit()
                        incident_count += 1
                        print(f"  ✅ {title} -> {db.query(Service).get(service_id).name}")
                
                except Exception as e:
                    print(f"  ❌ Error processing issue: {e}")
                    continue
            
            print(f"✅ Ingested {incident_count} incidents")
            return incident_count
        
        finally:
            db.close()

if __name__ == "__main__":
    connector = SentryConnector()
    connector.ingest_incidents(repo_id=1)