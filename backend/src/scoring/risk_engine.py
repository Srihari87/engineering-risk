from datetime import datetime, timedelta, timezone
from src.db.connection import SessionLocal
from src.models.models import Service, Incident, Commit, Dependency, Owner
from sqlalchemy import func

class RiskScoringEngine:
    """
    Deterministic risk scoring formula.
    
    Risk Score (0-10):
    = 0.30 * incident_density_score
    + 0.25 * ownership_gap_score
    + 0.20 * dependency_criticality_score
    + 0.15 * change_velocity_score
    + 0.10 * test_coverage_gap_score
    """
    
    def __init__(self):
        self.db = SessionLocal()
    
    def score_service(self, service_id: int) -> dict:
        """Calculate risk score for a service"""
        service = self.db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            return {"error": "Service not found"}
        
        # Calculate individual scores
        incident_score = self._score_incident_density(service_id)
        ownership_score = self._score_ownership_clarity(service_id)
        dependency_score = self._score_dependency_criticality(service_id)
        velocity_score = self._score_change_velocity(service_id)
        coverage_score = self._score_test_coverage(service_id)
        
        # Weighted sum
        total_score = (
            0.30 * incident_score +
            0.25 * ownership_score +
            0.20 * dependency_score +
            0.15 * velocity_score +
            0.10 * coverage_score
        )
        
        # Round to 1 decimal
        total_score = round(total_score, 1)
        
        return {
            "service_id": service_id,
            "service_name": service.name,
            "risk_score": total_score,
            "risk_level": self._risk_level(total_score),
            "breakdown": {
                "incident_density": round(incident_score, 1),
                "ownership_clarity": round(ownership_score, 1),
                "dependency_criticality": round(dependency_score, 1),
                "change_velocity": round(velocity_score, 1),
                "test_coverage": round(coverage_score, 1),
            },
            "details": {
                "incidents_90d": self._count_incidents_90d(service_id),
                "ownership_clarity": self._ownership_clarity_text(service_id),
                "dependent_services": self._count_dependent_services(service_id),
                "commits_90d": self._count_commits_90d(service_id),
            }
        }
    
    def _score_incident_density(self, service_id: int) -> float:
        """
        Score based on incidents in last 90 days.
        0 incidents = 0/10
        10+ incidents = 10/10
        """
        count = self._count_incidents_90d(service_id)
        
        # Linear: 1 incident per 10 = 1 point
        score = min(10, count)
        return score
    
    def _score_ownership_clarity(self, service_id: int) -> float:
        """
        Score based on ownership clarity.
        1 clear owner = 0/10 (good)
        0 owners = 10/10 (bad - ownership gap)
        2+ owners = 5/10 (ambiguous)
        """
        owners = self.db.query(Owner).filter(
            Owner.service_id == service_id,
            Owner.is_primary == True
        ).count()
        
        if owners == 1:
            return 0  # Clear ownership
        elif owners == 0:
            return 10  # Ownership gap
        else:
            return 5  # Ambiguous
    
    def _score_dependency_criticality(self, service_id: int) -> float:
        """
        Score based on how many services depend on this one.
        0 dependents = 0/10 (low criticality)
        10+ dependents = 10/10 (high criticality)
        """
        count = self._count_dependent_services(service_id)
        
        # Linear: 1 dependent = 1 point
        score = min(10, count)
        return score
    
    def _score_change_velocity(self, service_id: int) -> float:
        """
        Score based on commit frequency in last 90 days.
        0 commits = 0/10 (stable, low risk)
        40+ commits = 10/10 (high velocity, high risk)
        """
        count = self._count_commits_90d(service_id)
        
        # Linear: 1 commit per 4 = 1 point (more changes = more risk)
        score = min(10, count / 4)
        return score
    
    def _score_test_coverage(self, service_id: int) -> float:
        """
        Score based on test coverage gap.
        85%+ coverage = 0/10 (good)
        <50% coverage = 10/10 (bad)
        
        For MVP, we estimate based on commit count:
        High commit velocity + no explicit test data = assume low coverage
        """
        commits = self._count_commits_90d(service_id)
        
        # Heuristic: very high velocity suggests untested changes
        if commits > 30:
            return 7  # Likely low coverage
        elif commits > 10:
            return 3  # Moderate velocity
        else:
            return 1  # Low velocity, probably stable
    
    def _count_incidents_90d(self, service_id: int) -> int:
        """Count incidents in last 90 days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        
        count = self.db.query(Incident).filter(
            Incident.service_id == service_id,
            Incident.first_seen >= cutoff
        ).count()
        
        return count
    
    def _count_dependent_services(self, service_id: int) -> int:
        """Count services that depend on this service"""
        count = self.db.query(Dependency).filter(
            Dependency.from_service_id == service_id
        ).count()
        
        return count
    
    def _count_commits_90d(self, service_id: int) -> int:
        """Count commits touching this service in last 90 days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        
        count = self.db.query(Commit).filter(
            Commit.repo_id == self._get_repo_id(service_id),
            Commit.timestamp >= cutoff
        ).count()
        
        return count
    
    def _get_repo_id(self, service_id: int) -> int:
        """Get repo ID from service"""
        service = self.db.query(Service).filter(Service.id == service_id).first()
        return service.repo_id if service else None
    
    def _ownership_clarity_text(self, service_id: int) -> str:
        """Get text description of ownership clarity"""
        owners = self.db.query(Owner).filter(
            Owner.service_id == service_id,
            Owner.is_primary == True
        ).all()
        
        if len(owners) == 0:
            return "No owner assigned (gap)"
        elif len(owners) == 1:
            return f"Clear: {owners[0].owner_login}"
        else:
            names = [o.owner_login for o in owners]
            return f"Ambiguous: {', '.join(names)}"
    
    def _risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score < 3:
            return "low"
        elif score < 6:
            return "medium"
        elif score < 8:
            return "high"
        else:
            return "critical"
    
    def score_all_services(self, repo_id: int) -> list:
        """Score all services in a repo"""
        services = self.db.query(Service).filter(Service.repo_id == repo_id).all()
        
        scores = []
        for service in services:
            score = self.score_service(service.id)
            scores.append(score)
        
        # Sort by risk score (highest first)
        scores.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return scores
    
    def close(self):
        """Close database connection"""
        self.db.close()

if __name__ == "__main__":
    # Test scoring
    engine = RiskScoringEngine()
    
    # Score all services in repo 1
    print("🎯 Service Risk Scores\n")
    scores = engine.score_all_services(repo_id=1)
    
    for score in scores:
        print(f"{score['service_name']}: {score['risk_score']}/10 ({score['risk_level']})")
        print(f"  Incidents (90d): {score['details']['incidents_90d']}")
        print(f"  Ownership: {score['details']['ownership_clarity']}")
        print(f"  Dependents: {score['details']['dependent_services']}")
        print(f"  Commits (90d): {score['details']['commits_90d']}")
        print()
    
    engine.close()