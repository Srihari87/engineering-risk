import re
from datetime import datetime
from src.db.connection import SessionLocal
from src.models.models import File, CodeEntity

class TreeSitterParser:
    def __init__(self):
        pass
    
    def get_language(self, file_path: str):
        """Detect language from file extension"""
        ext = file_path.split('.')[-1].lower()
        
        if ext in ['py']:
            return 'python'
        elif ext in ['ts', 'tsx', 'js', 'jsx']:
            return 'typescript'
        elif ext in ['go']:
            return 'go'
        else:
            return None
    
    def parse_file(self, file_path: str, content: str):
        """Parse a file using regex (simple MVP approach)"""
        language = self.get_language(file_path)
        
        if language == 'python':
            return self._extract_python(content)
        elif language == 'typescript':
            return self._extract_typescript(content)
        
        return None
    
    def _extract_python(self, content: str):
        """Extract Python functions and classes using regex"""
        entities = []
        lines = content.split('\n')
        
        # Find functions
        func_pattern = r'^def\s+(\w+)\s*\('
        class_pattern = r'^class\s+(\w+)\s*[\(:]'
        
        for i, line in enumerate(lines):
            # Match functions
            func_match = re.match(func_pattern, line)
            if func_match:
                entities.append({
                    'type': 'function',
                    'name': func_match.group(1),
                    'start_line': i + 1,
                    'end_line': i + 1,
                    'calls': [],
                    'called_by': []
                })
            
            # Match classes
            class_match = re.match(class_pattern, line)
            if class_match:
                entities.append({
                    'type': 'class',
                    'name': class_match.group(1),
                    'start_line': i + 1,
                    'end_line': i + 1,
                    'calls': [],
                    'called_by': []
                })
        
        return entities
    
    def _extract_typescript(self, content: str):
        """Extract TypeScript functions and classes using regex"""
        entities = []
        lines = content.split('\n')
        
        # Find functions
        func_pattern = r'(function|const|let|var)\s+(\w+)\s*[=\(:]'
        class_pattern = r'class\s+(\w+)\s*[\{]'
        
        for i, line in enumerate(lines):
            # Match functions
            func_match = re.search(func_pattern, line)
            if func_match:
                entities.append({
                    'type': 'function',
                    'name': func_match.group(2),
                    'start_line': i + 1,
                    'end_line': i + 1,
                    'calls': [],
                    'called_by': []
                })
            
            # Match classes
            class_match = re.search(class_pattern, line)
            if class_match:
                entities.append({
                    'type': 'class',
                    'name': class_match.group(1),
                    'start_line': i + 1,
                    'end_line': i + 1,
                    'calls': [],
                    'called_by': []
                })
        
        return entities
    
    def store_entities(self, file_id: int, entities: list):
        """Store extracted entities in database"""
        if not entities:
            return 0
        
        db = SessionLocal()
        count = 0
        
        try:
            for entity in entities:
                code_entity = CodeEntity(
                    file_id=file_id,
                    type=entity['type'],
                    name=entity['name'],
                    start_line=entity['start_line'],
                    end_line=entity['end_line'],
                    calls_text=str(entity.get('calls', [])),
                    called_by_text=str(entity.get('called_by', []))
                )
                db.add(code_entity)
                count += 1
            
            db.commit()
            return count
        except Exception as e:
            print(f"❌ Error storing entities: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

if __name__ == "__main__":
    # Test parsing
    parser = TreeSitterParser()
    
    # Example: parse a Python file
    test_code = """
def hello_world():
    print("Hello")

class MyClass:
    def method(self):
        pass
"""
    
    entities = parser.parse_file("test.py", test_code)
    
    if entities:
        print(f"✅ Found {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity['type']}: {entity['name']} (line {entity['start_line']})")
    else:
        print("❌ No entities found")