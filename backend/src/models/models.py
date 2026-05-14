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
    
    services = relationship("Service", back_populates="repo", cascade="all, delete-orphan")
    files = relationship("File", back_populates="repo", cascade="all, delete-orphan")
    commits = relationship("Commit", back_populates="repo", cascade="all, delete-orphan")

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