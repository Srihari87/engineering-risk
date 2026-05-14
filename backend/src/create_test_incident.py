from src.db.connection import SessionLocal
from src.models.models import Incident
from datetime import datetime, timedelta

db = SessionLocal()

# Create a test incident
incident = Incident(
    repo_id=1,
    service_id=1,
    sentry_id="test-incident-1",
    title="TimeoutError in payment retry",
    error_type="TimeoutError",
    stack_trace="File 'backend/src/connectors/github_connector.py', line 50",
    file_path="backend/src/connectors/github_connector.py",
    first_seen=datetime.utcnow() - timedelta(days=10),
    last_seen=datetime.utcnow() - timedelta(days=2),
    occurrence_count=5,
    is_resolved=False
)
db.add(incident)
db.commit()

print(f"✅ Created test incident: {incident.title}")

db.close()