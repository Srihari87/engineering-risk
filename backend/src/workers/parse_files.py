from src.db.connection import SessionLocal
from src.models.models import File, Repo
from src.parsers.tree_sitter_parser import TreeSitterParser
from src.connectors.github_connector import GitHubConnector
import hashlib

def parse_repo_files(repo_id: int, owner: str, repo_name: str):
    """Parse all files in a repo"""
    db = SessionLocal()
    parser = TreeSitterParser()
    connector = GitHubConnector()
    
    try:
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo:
            print(f"❌ Repo {repo_id} not found")
            return
        
        print(f"📂 Parsing files in {repo.full_name}...")
        
        # List of common code files to parse
        code_files = [
            'src/main.py',
            'src/config.py',
            'src/db/connection.py',
            'src/models/models.py',
            'src/api/routes.py',
            'src/connectors/github_connector.py',
            'src/parsers/tree_sitter_parser.py',
        ]
        
        parsed_count = 0
        
        for file_path in code_files:
            print(f"  📄 Parsing {file_path}...")
            
            try:
                # Fetch file content
                file_content = connector._fetch_file_content(owner, repo_name, file_path)
                
                if not file_content:
                    print(f"    ⚠️ File not found")
                    continue
                
                # Calculate hash
                file_hash = hashlib.sha256(file_content.encode()).hexdigest()
                
                # Check if file already exists
                existing = db.query(File).filter(
                    File.repo_id == repo_id,
                    File.path == file_path
                ).first()
                
                if existing:
                    file_obj = existing
                else:
                    file_obj = File(
                        repo_id=repo_id,
                        path=file_path,
                        language=parser.get_language(file_path),
                        file_hash=file_hash,
                        size_bytes=len(file_content),
                        is_parseable=True,
                        parse_status='pending'
                    )
                    db.add(file_obj)
                    db.commit()
                
                # Parse the file
                entities = parser.parse_file(file_path, file_content)
                
                if entities:
                    stored = parser.store_entities(file_obj.id, entities)
                    file_obj.parse_status = 'success'
                    file_obj.is_parseable = True
                    parsed_count += stored
                    print(f"    ✅ Found {stored} entities")
                else:
                    file_obj.parse_status = 'no_entities'
                    print(f"    ⚠️ No entities found")
                
                db.commit()
            
            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue
        
        print(f"✅ Total: {parsed_count} entities parsed")
    
    finally:
        db.close()

if __name__ == "__main__":
    # Test: parse your repo
    parse_repo_files(repo_id=1, owner="Srihari87", repo_name="engineering-risk")