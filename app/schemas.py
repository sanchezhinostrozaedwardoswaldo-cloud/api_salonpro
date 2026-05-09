from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class UsuarioBase(BaseModel):
    nombre: str
    email: str
    rol: str = "empleado"
    activo: int = 1

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioResponse(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: Optional[str] = None


class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: Optional[str] = None


class CitaBase(BaseModel):
    cliente_id: int
    usuario_id: int
    servicio: str
    fecha: str
    hora: str
    duracion_min: int = 30
    estado: str = "pendiente"
    precio: Optional[float] = None
    notas: Optional[str] = None

class CitaCreate(CitaBase):
    pass

class CitaUpdate(BaseModel):
    estado: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None
    precio: Optional[float] = None
    notas: Optional[str] = None

class CitaResponse(CitaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: Optional[str] = None
    cliente: Optional[ClienteResponse] = None
    usuario: Optional[UsuarioResponse] = None


class TareaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    asignado_a: Optional[int] = None
    prioridad: str = "media"
    estado: str = "pendiente"
    fecha_limite: Optional[str] = None

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    asignado_a: Optional[int] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    fecha_limite: Optional[str] = None

class TareaResponse(TareaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    asignado: Optional[UsuarioResponse] = None


class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str