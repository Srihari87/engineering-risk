from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base

class Repo(Base):
    __tablename__ = "repos"
    
    id = Column(BigInteger, primary_key=True)
    github_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    owner_login = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    default_branch = Column(String(255), default="main")
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = relationship("Service", back_populates="repo", cascade="all, delete-orphan")
    files = relationship("File", back_populates="repo", cascade="all, delete-orphan")
    commits = relationship("Commit", back_populates="repo", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="repo", cascade="all, delete-orphan")  # ADD THIS LINE

class Service(Base):
    __tablename__ = "services"
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, ForeignKey("repos.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    critical_flag = Column(Boolean, default=False)
    sla_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    repo = relationship("Repo", back_populates="services")
    files = relationship("File", back_populates="service")
    owners = relationship("Owner", back_populates="service", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="service")

class File(Base):
    __tablename__ = "files"
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, ForeignKey("repos.id"), nullable=False)
    service_id = Column(BigInteger, ForeignKey("services.id", ondelete="SET NULL"))
    path = Column(String(1024), nullable=False)
    language = Column(String(50))
    file_hash = Column(String(64), nullable=False)
    size_bytes = Column(Integer)
    is_parseable = Column(Boolean, default=True)
    parse_status = Column(String(50), default="pending")
    last_parsed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    repo = relationship("Repo", back_populates="files")
    service = relationship("Service", back_populates="files")
    code_entities = relationship("CodeEntity", back_populates="file", cascade="all, delete-orphan")

class Owner(Base):
    __tablename__ = "owners"
    
    id = Column(BigInteger, primary_key=True)
    service_id = Column(BigInteger, ForeignKey("services.id"), nullable=False)
    owner_login = Column(String(255), nullable=False)
    owner_type = Column(String(50))
    source = Column(String(50))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    service = relationship("Service", back_populates="owners")

class Commit(Base):
    __tablename__ = "commits"
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, ForeignKey("repos.id"), nullable=False)
    git_hash = Column(String(40), unique=True, nullable=False)
    author_login = Column(String(255))
    author_email = Column(String(255))
    message = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    is_merge = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repo = relationship("Repo", back_populates="commits")

class Dependency(Base):
    __tablename__ = "dependencies"
    
    id = Column(BigInteger, primary_key=True)
    from_service_id = Column(BigInteger, ForeignKey("services.id"), nullable=False)
    to_service_id = Column(BigInteger, ForeignKey("services.id"), nullable=False)
    is_critical = Column(Boolean, default=False)
    example_code_path = Column(Text)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    
    from_service = relationship("Service", foreign_keys=[from_service_id])
    to_service = relationship("Service", foreign_keys=[to_service_id])
    
class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, ForeignKey("repos.id"), nullable=False)
    service_id = Column(BigInteger, ForeignKey("services.id"), nullable=False)
    sentry_id = Column(String(255), unique=True)
    title = Column(String(512))
    error_type = Column(String(255))
    stack_trace = Column(Text)
    file_path = Column(String(1024))
    function_name = Column(String(255))
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    occurrence_count = Column(Integer, default=1)
    is_resolved = Column(Boolean, default=False)
    resolution_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repo = relationship("Repo", back_populates="incidents")
    service = relationship("Service", back_populates="incidents")

class CodeEntity(Base):
    __tablename__ = "code_entities"
    
    id = Column(BigInteger, primary_key=True)
    file_id = Column(BigInteger, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50))  # 'function', 'class', 'method'
    name = Column(String(255), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    calls_text = Column(Text)  # JSON array of function calls
    called_by_text = Column(Text)  # JSON array of callers
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    file = relationship("File", back_populates="code_entities")