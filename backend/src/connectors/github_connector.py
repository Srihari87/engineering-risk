import requests
from datetime import datetime, timezone
from src.db.connection import SessionLocal
from src.models.models import Repo, Commit
from src.config import config

class GitHubConnector:
    def __init__(self):
        self.token = config.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
    
    def get_repo(self, owner: str, repo_name: str):
        """Fetch repo metadata from GitHub"""
        url = f"{self.base_url}/repos/{owner}/{repo_name}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Error fetching repo: {response.status_code}")
            return None
        
        return response.json()
    
    def get_commits(self, owner: str, repo_name: str, since: datetime = None):
        """Fetch commits from GitHub"""
        url = f"{self.base_url}/repos/{owner}/{repo_name}/commits"
        
        params = {
            "per_page": 100,
            "page": 1
        }
        
        if since:
            params["since"] = since.isoformat()
        
        all_commits = []
        
        while True:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Error fetching commits: {response.status_code}")
                break
            
            commits = response.json()
            
            if not commits:
                break
            
            all_commits.extend(commits)
            params["page"] += 1
        
        return all_commits
    
    def get_files(self, owner: str, repo_name: str, path: str = ""):
        """Fetch files from a repo"""
        url = f"{self.base_url}/repos/{owner}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
        
        return response.json()
    
    def ingest_repo(self, owner: str, repo_name: str):
        """Full ingestion: repo + commits"""
        db = SessionLocal()
        
        try:
            # Fetch repo metadata
            print(f"📦 Fetching {owner}/{repo_name}...")
            repo_data = self.get_repo(owner, repo_name)
            
            if not repo_data:
                return False
            
            # Store repo in DB
            repo = Repo(
                github_id=repo_data["id"],
                name=repo_data["name"],
                full_name=repo_data["full_name"],
                owner_login=repo_data["owner"]["login"],
                url=repo_data["html_url"],
                default_branch=repo_data["default_branch"],
                is_active=not repo_data["archived"],
                last_synced_at=datetime.now(timezone.utc)
            )
            db.add(repo)
            db.commit()
            print(f"✅ Repo stored: {repo.full_name} (ID: {repo.id})")
            
            # Fetch commits
            print(f"📝 Fetching commits...")
            commits_data = self.get_commits(owner, repo_name)
            
            commit_count = 0
            for commit_data in commits_data[:100]:  # Limit to 100 for MVP
                commit = Commit(
                    repo_id=repo.id,
                    git_hash=commit_data["sha"],
                    author_login=commit_data.get("author", {}).get("login"),
                    author_email=commit_data.get("commit", {}).get("author", {}).get("email"),
                    message=commit_data.get("commit", {}).get("message"),
                    timestamp=datetime.fromisoformat(
                        commit_data.get("commit", {}).get("author", {}).get("date", "").replace("Z", "+00:00")
                    ),
                    is_merge=len(commit_data.get("parents", [])) > 1
                )
                db.add(commit)
                commit_count += 1
            
            db.commit()
            print(f"✅ Stored {commit_count} commits")
            
            return True
        
        except Exception as e:
            print(f"❌ Error: {e}")
            db.rollback()
            return False
        
        finally:
            db.close()

if __name__ == "__main__":
    connector = GitHubConnector()
    
    # Example: ingest your own repo
    owner = "Srihari87"
    repo = "engineering-risk"
    
    success = connector.ingest_repo(owner, repo)
    
    if success:
        print("✅ Ingestion complete!")
    else:
        print("❌ Ingestion failed")