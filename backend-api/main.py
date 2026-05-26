import os
import time
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional

# ----------------------------------------------------
# 1. DATABASE SETUP
# ----------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:supersecretpassword@db:5432/superdashboard")

# Retry logic for connecting to DB on startup (useful in docker compose)
engine = None
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as conn:
            break
    except Exception as e:
        print(f"Database connection attempt {i+1} failed. Retrying in 3 seconds... Error: {e}")
        time.sleep(3)

if not engine:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class Perfil(Base):
    __tablename__ = "perfis"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cargo = Column(String(100), nullable=False)
    idade = Column(Integer, nullable=False)
    notas = Column(Text, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------
# 2. PYDANTIC SCHEMAS
# ----------------------------------------------------
class PerfilBase(BaseModel):
    nome: str
    cargo: str
    idade: int
    notas: Optional[str] = None

class PerfilCreate(PerfilBase):
    pass

class PerfilResponse(PerfilBase):
    id: int

    class Config:
        from_attributes = True

# ----------------------------------------------------
# 3. FASTAPI APP INITIALIZATION
# ----------------------------------------------------
app = FastAPI(
    title="Jarvis V1 API",
    description="Backend API for managing user profiles",
    version="1.0.0"
)

# Enable CORS for frontend connection (Eel app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# 4. REST API ROUTES
# ----------------------------------------------------

@app.get("/")
def get_status():
    """System health check endpoint"""
    # Reads PORT environment variable
    _port = os.environ.get("PORT", "2001")
    return {
        "status": "Online",
        "sistema": "Jarvis V1"
    }

@app.post("/perfis", response_model=PerfilResponse, status_code=status.HTTP_201_CREATED)
def create_perfil(perfil: PerfilCreate, db: Session = Depends(get_db)):
    """Create a new user profile"""
    db_perfil = Perfil(
        nome=perfil.nome,
        cargo=perfil.cargo,
        idade=perfil.idade,
        notas=perfil.notas
    )
    db.add(db_perfil)
    db.commit()
    db.refresh(db_perfil)
    return db_perfil

@app.get("/perfis", response_model=List[PerfilResponse])
def read_perfis(db: Session = Depends(get_db)):
    """Retrieve all user profiles"""
    return db.query(Perfil).all()

if __name__ == "__main__":
    # Vai buscar a porta 2001 definida no Docker, ou usa 2001 por defeito
    porta = int(os.environ.get("PORT", 2001)) 
    uvicorn.run("main:app", host="0.0.0.0", port=porta, reload=True)
