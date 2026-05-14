from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.connection import get_db
from src.models.models import Service, Incident
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/services/{service_id}/risk")
def get_service_risk(service_id: int, db: Session = Depends(get_db)):
    """Get service risk metrics"""
    service = db.query(Service).filter(Service.id == service_id).first()
    
    if not service:
        return {"error": "Service not found"}
    
    # Count incidents in last 90 days
    incidents_90d = db.query(Incident).filter(
        Incident.service_id == service_id,
        Incident.first_seen >= datetime.utcnow() - timedelta(days=90)
    ).count()
    
    return {
        "service_id": service_id,
        "name": service.name,
        "critical": service.critical_flag,
        "sla_minutes": service.sla_minutes,
        "incidents_90d": incidents_90d,
        "status": "operational",
    }

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "0.1.0"}