from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from database import Base

class Dossier(Base):
    __tablename__ = "dossiers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    classification = Column(String)
    threat_level = Column(String)
    role = Column(String)
    strengths = Column(Text)
    weaknesses = Column(Text)
    notes = Column(Text)

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Shortcut(Base):
    __tablename__ = "shortcuts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    command_or_path = Column(String)
    description = Column(Text)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key_value = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Integer, default=1) # Boolean equivalent for SQLite/Postgres compatibility
    
    # Scope-based Permissions (RBAC)
    allow_get = Column(Integer, default=1)
    allow_post = Column(Integer, default=0)
    allow_put = Column(Integer, default=0)
    allow_delete = Column(Integer, default=0)
    allow_admin = Column(Integer, default=0)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_avg = Column(Float)
    ram_avg = Column(Float)
    os_target = Column(String)

class UserAccount(Base):
    __tablename__ = "user_accounts"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class VaultRegistry(Base):
    __tablename__ = "vaults_registry"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    path = Column(String)
    security_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True)
    is_pinned = Column(Integer, default=0) # SQLite compat boolean
    is_favorite = Column(Integer, default=0)
    is_hidden = Column(Integer, default=0)
