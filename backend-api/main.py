from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Form, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database import engine, get_db, Base
import models, schemas, seed
from security import get_current_user, create_access_token
from templates import LOGIN_HTML, DASHBOARD_HTML
import hashlib


# Disable default docs because we want to protect them
app = FastAPI(title="Vexylo API", docs_url=None, redoc_url=None, openapi_url=None)

# Mount static files for swagger CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to localhost origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed.seed_database(db)

# --- VISUAL AND AUTH ROUTES ---

@app.get("/", response_class=HTMLResponse)
def get_login():
    """
    Returns the custom login form (completely open).
    """
    return LOGIN_HTML

@app.get("/api", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    Returns the custom dashboard if authenticated, otherwise redirects to /.
    """
    try:
        # Check if the user is authenticated using the global dependency logic
        await get_current_user(request)
        return DASHBOARD_HTML
    except HTTPException:
        # If not authenticated, redirect to the login page
        return RedirectResponse(url="/", status_code=302)

@app.get("/api/has-account")
def has_account(db: Session = Depends(get_db)):
    existing = db.query(models.UserAccount).first()
    if existing:
        return {"has_account": True, "username": existing.username}
    return {"has_account": False}

@app.post("/api/register")
def register(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(models.UserAccount).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists")
    
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    user = models.UserAccount(username=username, password_hash=pw_hash)
    db.add(user)
    db.commit()
    return {"success": True}

@app.post("/api/login")
def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.UserAccount).filter(models.UserAccount.username == username).first()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if not user or user.password_hash != pw_hash:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": username})
    
    # Return success but also set the cookie
    response = JSONResponse(content={"message": "Successfully logged in"})
    response.set_cookie(
        key="session_token", 
        value=access_token, 
        httponly=True, 
        max_age=3600, # 1 hour
        samesite="lax",
        secure=False
    )
    return response

@app.post("/api/logout")
def logout(response: Response):
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="session_token")
    return response

@app.get("/api/verify-key")
def verify_key(request: Request, db: Session = Depends(get_db)):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    db_key = db.query(models.ApiKey).filter(models.ApiKey.key_value == api_key).first()
    if not db_key or db_key.active != 1:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    if not db_key.allow_admin:
        raise HTTPException(status_code=403, detail="API Key does not have admin permissions")
    
    return {"success": True, "valid": True, "name": db_key.name}

# --- PROTECTED SWAGGER ROUTES ---

@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(username: str = Depends(get_current_user)):
    return JSONResponse(get_openapi(title="Vexylo API", version="1.0.0", routes=app.routes))

@app.get("/api/docs", include_in_schema=False)
async def get_documentation(username: str = Depends(get_current_user)):
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json", 
        title="Vexylo API - Protected Docs",
        swagger_css_url="/static/swagger-ui.min.css"
    )


# --- PROTECTED API ROUTES ---

# Create a router with the global security dependency for all data endpoints
api_router = APIRouter(dependencies=[Depends(get_current_user)])

# Dossiers Routes
@api_router.get("/api/dossiers", response_model=List[schemas.DossierResponse])
def get_dossiers(classification: Optional[str] = None, threat_level: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Dossier)
    if classification:
        query = query.filter(models.Dossier.classification == classification)
    if threat_level:
        query = query.filter(models.Dossier.threat_level == threat_level)
    return query.all()

@api_router.post("/api/dossiers", response_model=schemas.DossierResponse)
def create_dossier(dossier: schemas.DossierCreate, db: Session = Depends(get_db)):
    db_dossier = models.Dossier(**dossier.dict())
    db.add(db_dossier)
    db.commit()
    db.refresh(db_dossier)
    return db_dossier

@api_router.put("/api/dossiers/{dossier_id}", response_model=schemas.DossierResponse)
def update_dossier(dossier_id: int, dossier: schemas.DossierCreate, db: Session = Depends(get_db)):
    db_dossier = db.query(models.Dossier).filter(models.Dossier.id == dossier_id).first()
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")
    for key, value in dossier.dict().items():
        setattr(db_dossier, key, value)
    db.commit()
    db.refresh(db_dossier)
    return db_dossier

@api_router.delete("/api/dossiers/{dossier_id}")
def delete_dossier(dossier_id: int, db: Session = Depends(get_db)):
    db_dossier = db.query(models.Dossier).filter(models.Dossier.id == dossier_id).first()
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")
    db.delete(db_dossier)
    db.commit()
    return {"detail": "Deleted successfully"}

# Notes Routes
@api_router.get("/api/notes", response_model=List[schemas.NoteResponse])
def get_notes(db: Session = Depends(get_db)):
    return db.query(models.Note).order_by(models.Note.timestamp.desc()).all()

@api_router.post("/api/notes", response_model=schemas.NoteResponse)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    db_note = models.Note(**note.dict())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@api_router.delete("/api/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(db_note)
    db.commit()
    return {"detail": "Deleted successfully"}

# Shortcuts Routes
@api_router.get("/api/shortcuts", response_model=List[schemas.ShortcutResponse])
def get_shortcuts(db: Session = Depends(get_db)):
    return db.query(models.Shortcut).all()

@api_router.post("/api/shortcuts", response_model=schemas.ShortcutResponse)
def create_shortcut(shortcut: schemas.ShortcutCreate, db: Session = Depends(get_db)):
    db_shortcut = models.Shortcut(**shortcut.dict())
    db.add(db_shortcut)
    db.commit()
    db.refresh(db_shortcut)
    return db_shortcut

@api_router.delete("/api/shortcuts/{shortcut_id}")
def delete_shortcut(shortcut_id: int, db: Session = Depends(get_db)):
    db_shortcut = db.query(models.Shortcut).filter(models.Shortcut.id == shortcut_id).first()
    if not db_shortcut:
        raise HTTPException(status_code=404, detail="Shortcut not found")
    db.delete(db_shortcut)
    db.commit()
    return {"detail": "Deleted successfully"}

# Vaults Registry Routes
@api_router.get("/api/vaults", response_model=List[schemas.VaultRegistryResponse])
def get_vaults(db: Session = Depends(get_db)):
    return db.query(models.VaultRegistry).all()

@api_router.post("/api/vaults", response_model=schemas.VaultRegistryResponse)
def create_vault(vault: schemas.VaultRegistryCreate, db: Session = Depends(get_db)):
    db_vault = models.VaultRegistry(**vault.dict())
    db.add(db_vault)
    db.commit()
    db.refresh(db_vault)
    return db_vault

# File Metadata Routes
@api_router.get("/api/file-metadata", response_model=List[schemas.FileMetadataResponse])
def get_file_metadata(db: Session = Depends(get_db)):
    return db.query(models.FileMetadata).all()

@api_router.post("/api/file-metadata/toggle-pin")
def toggle_pin(path: str = Query(...), db: Session = Depends(get_db)):
    meta = db.query(models.FileMetadata).filter(models.FileMetadata.path == path).first()
    if not meta:
        meta = models.FileMetadata(path=path, is_pinned=1)
        db.add(meta)
    else:
        meta.is_pinned = 0 if meta.is_pinned else 1
    db.commit()
    return {"success": True, "is_pinned": bool(meta.is_pinned)}

@api_router.post("/api/file-metadata/toggle-favorite")
def toggle_favorite(path: str = Query(...), db: Session = Depends(get_db)):
    meta = db.query(models.FileMetadata).filter(models.FileMetadata.path == path).first()
    if not meta:
        meta = models.FileMetadata(path=path, is_favorite=1)
        db.add(meta)
    else:
        meta.is_favorite = 0 if meta.is_favorite else 1
    db.commit()
    return {"success": True, "is_favorite": bool(meta.is_favorite)}

@api_router.post("/api/file-metadata/toggle-hidden")
def toggle_hidden(path: str = Query(...), db: Session = Depends(get_db)):
    meta = db.query(models.FileMetadata).filter(models.FileMetadata.path == path).first()
    if not meta:
        meta = models.FileMetadata(path=path, is_hidden=1)
        db.add(meta)
    else:
        meta.is_hidden = 0 if meta.is_hidden else 1
    db.commit()
    return {"success": True, "is_hidden": bool(meta.is_hidden)}

# System Routes (Replaces Nomad OS)
# Global variable to store Host OS info provided by the frontend
HOST_OS_INFO = {
    "os": "Pending Frontend Registration...",
    "distro": "Pending...",
    "package_manager": "Pending..."
}

class OSInfoRequest(schemas.BaseModel):
    os: str
    distro: str
    package_manager: str

@api_router.post("/api/system/os")
def register_os_info(info: OSInfoRequest):
    global HOST_OS_INFO
    HOST_OS_INFO["os"] = info.os
    HOST_OS_INFO["distro"] = info.distro
    HOST_OS_INFO["package_manager"] = info.package_manager
    return {"success": True, "detail": "Host OS registered successfully."}

@api_router.get("/api/system/os")
def get_os_info():
    return HOST_OS_INFO

@api_router.post("/api/system/logs", response_model=schemas.SystemLogResponse)
def create_system_log(log: schemas.SystemLogCreate, db: Session = Depends(get_db)):
    db_log = models.SystemLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# --- SETTINGS & CREDENTIALS ---

import security

@api_router.post("/api/settings/update-credentials")
def update_credentials(creds: schemas.UpdateCredentialsRequest, db: Session = Depends(get_db)):
    user = db.query(models.UserAccount).filter(models.UserAccount.username == creds.username).first()
    if user:
        user.password_hash = hashlib.sha256(creds.password.encode()).hexdigest()
        db.commit()
        return {"success": True, "detail": "Credentials updated in DB."}
    return {"success": False, "detail": "User not found."}

# --- API KEYS ---
import uuid

@api_router.get("/api/keys", response_model=List[schemas.ApiKeyResponse])
def get_api_keys(db: Session = Depends(get_db)):
    return db.query(models.ApiKey).filter(models.ApiKey.active == 1).all()

@api_router.post("/api/keys", response_model=schemas.ApiKeyResponse)
def create_api_key(key_in: schemas.ApiKeyCreate, db: Session = Depends(get_db)):
    new_key_value = str(uuid.uuid4())
    db_key = models.ApiKey(
        name=key_in.name, 
        key_value=new_key_value,
        allow_get=int(key_in.allow_get),
        allow_post=int(key_in.allow_post),
        allow_put=int(key_in.allow_put),
        allow_delete=int(key_in.allow_delete),
        allow_admin=int(key_in.allow_admin)
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

@api_router.delete("/api/keys/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    db_key = db.query(models.ApiKey).filter(models.ApiKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    # Soft delete
    db_key.active = 0
    db.commit()
    return {"success": True, "detail": "API Key invalidated"}

# Register the protected router to the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2060)
