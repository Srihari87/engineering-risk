from src.db.connection import SessionLocal
from src.models.models import Service, Owner

db = SessionLocal()

# Create a test service
service = Service(
    repo_id=1,
    name="payment-service",
    description="Handles payment processing",
    critical_flag=True,
    sla_minutes=5
)
db.add(service)
db.commit()

# Add an owner
owner = Owner(
    service_id=service.id,
    owner_login="platform-payments",
    source="codeowners",
    is_primary=True
)
db.add(owner)
db.commit()

print(f"✅ Created service: {service.name} (ID: {service.id})")

db.close()