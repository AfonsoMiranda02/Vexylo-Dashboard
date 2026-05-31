from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DossierBase(BaseModel):
    name: str
    classification: Optional[str] = None
    threat_level: Optional[str] = None
    role: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    notes: Optional[str] = None

class DossierCreate(DossierBase):
    pass

class DossierResponse(DossierBase):
    id: int
    
    class Config:
        from_attributes = True

class NoteBase(BaseModel):
    content: str

class NoteCreate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ShortcutBase(BaseModel):
    name: str
    command_or_path: str
    description: Optional[str] = None

class ShortcutCreate(ShortcutBase):
    pass

class ShortcutResponse(ShortcutBase):
    id: int
    
    class Config:
        from_attributes = True

class ApiKeyBase(BaseModel):
    name: str
    allow_get: bool = True
    allow_post: bool = False
    allow_put: bool = False
    allow_delete: bool = False
    allow_admin: bool = False

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyResponse(ApiKeyBase):
    id: int
    key_value: str
    created_at: datetime
    active: int

    class Config:
        from_attributes = True

class SystemLogCreate(BaseModel):
    cpu_avg: float
    ram_avg: float
    os_target: str

class SystemLogResponse(SystemLogCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class UpdateCredentialsRequest(BaseModel):
    username: str
    password: str
