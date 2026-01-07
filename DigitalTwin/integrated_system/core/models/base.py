"""
Base models for the integrated system.
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel as PydanticBaseModel, Field

# SQLAlchemy Base
Base = declarative_base()

class BaseDBModel(Base):
    """Base SQLAlchemy model with common fields."""
    
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class User(BaseDBModel):
    """User model."""
    
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    full_name = Column(String(100), nullable=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    data_sources = relationship("DataSource", back_populates="user")
    analysis_jobs = relationship("AnalysisJob", back_populates="user")
    
class DataSource(BaseDBModel):
    """Data source model."""
    
    __tablename__ = "data_sources"
    
    user_id = Column(String(36), ForeignKey("users.id"))
    name = Column(String(100))
    source_type = Column(String(50))  # email, messages, calendar, etc.
    connection_info = Column(JSON)
    last_sync = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="data_sources")
    data_batches = relationship("DataBatch", back_populates="data_source")
    
class DataBatch(BaseDBModel):
    """Data batch model."""
    
    __tablename__ = "data_batches"
    
    data_source_id = Column(String(36), ForeignKey("data_sources.id"))
    batch_type = Column(String(50))  # raw, processed, analyzed
    record_count = Column(Integer)
    storage_path = Column(String(255))  # Path to stored data
    metadata = Column(JSON)
    
    # Relationships
    data_source = relationship("DataSource", back_populates="data_batches")
    
class AnalysisJob(BaseDBModel):
    """Analysis job model."""
    
    __tablename__ = "analysis_jobs"
    
    user_id = Column(String(36), ForeignKey("users.id"))
    job_type = Column(String(50))  # communication, advanced, cognitive
    status = Column(String(20))  # pending, running, completed, failed
    parameters = Column(JSON)
    result_path = Column(String(255), nullable=True)  # Path to results
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analysis_jobs")
    insights = relationship("Insight", back_populates="analysis_job")
    
class Insight(BaseDBModel):
    """Insight model."""
    
    __tablename__ = "insights"
    
    analysis_job_id = Column(String(36), ForeignKey("analysis_jobs.id"))
    title = Column(String(100))
    description = Column(Text)
    category = Column(String(50))
    score = Column(Float)
    metadata = Column(JSON)
    
    # Relationships
    analysis_job = relationship("AnalysisJob", back_populates="insights")

# Pydantic models for API
class UserBase(PydanticBaseModel):
    """Base Pydantic model for User."""
    
    username: str
    email: str
    full_name: Optional[str] = None
    is_admin: bool = False
    
class UserCreate(UserBase):
    """Pydantic model for creating a User."""
    
    password: str
    
class UserUpdate(PydanticBaseModel):
    """Pydantic model for updating a User."""
    
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    
class UserResponse(UserBase):
    """Pydantic model for User response."""
    
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        
class DataSourceBase(PydanticBaseModel):
    """Base Pydantic model for DataSource."""
    
    name: str
    source_type: str
    connection_info: Dict[str, Any]
    
class DataSourceCreate(DataSourceBase):
    """Pydantic model for creating a DataSource."""
    
    pass
    
class DataSourceUpdate(PydanticBaseModel):
    """Pydantic model for updating a DataSource."""
    
    name: Optional[str] = None
    connection_info: Optional[Dict[str, Any]] = None
    
class DataSourceResponse(DataSourceBase):
    """Pydantic model for DataSource response."""
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        
class AnalysisJobBase(PydanticBaseModel):
    """Base Pydantic model for AnalysisJob."""
    
    job_type: str
    parameters: Dict[str, Any]
    
class AnalysisJobCreate(AnalysisJobBase):
    """Pydantic model for creating an AnalysisJob."""
    
    pass
    
class AnalysisJobResponse(AnalysisJobBase):
    """Pydantic model for AnalysisJob response."""
    
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class InsightBase(PydanticBaseModel):
    """Base Pydantic model for Insight."""
    
    title: str
    description: str
    category: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    
class InsightResponse(InsightBase):
    """Pydantic model for Insight response."""
    
    id: str
    analysis_job_id: str
    created_at: datetime
    
    class Config:
        orm_mode = True