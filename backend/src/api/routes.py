from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.connection import get_db
from src.models.models import Service, Incident
from datetime import datetime, timedelta
from src.models.models import Service, Incident, Repo, Commit

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

@router.get("/repos")
def get_repos(db: Session = Depends(get_db)):
    """Get all repos"""
    repos = db.query(Repo).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "full_name": r.full_name,
            "owner": r.owner_login,
            "url": r.url,
            "commits": len(r.commits)
        }
        for r in repos
    ]

@router.get("/repos/{repo_id}/commits")
def get_repo_commits(repo_id: int, db: Session = Depends(get_db)):
    """Get commits for a repo"""
    commits = db.query(Commit).filter(Commit.repo_id == repo_id).all()
    return [
        {
            "hash": c.git_hash,
            "author": c.author_login,
            "message": c.message,
            "timestamp": c.timestamp,
            "is_merge": c.is_merge
        }
        for c in commits
    ]

from src.scoring.risk_engine import RiskScoringEngine

@router.get("/services/{service_id}/risk-score")
def get_service_risk_score(service_id: int):
    """Get risk score for a service"""
    engine = RiskScoringEngine()
    score = engine.score_service(service_id)
    engine.close()
    return score

@router.get("/repos/{repo_id}/risk-scores")
def get_repo_risk_scores(repo_id: int):
    """Get risk scores for all services in a repo"""
    engine = RiskScoringEngine()
    scores = engine.score_all_services(repo_id)
    engine.close()
    return scores