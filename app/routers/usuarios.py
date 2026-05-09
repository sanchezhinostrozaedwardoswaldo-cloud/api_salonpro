from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioResponse
from app.dependencies import get_password_hash, require_role

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db), current_user=Depends(require_role(["admin"]))):
    return db.query(Usuario).all()

@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db), current_user=Depends(require_role(["admin"]))):
    db_user = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password=get_password_hash(usuario.password),
        rol=usuario.rol,
        activo=usuario.activo
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user