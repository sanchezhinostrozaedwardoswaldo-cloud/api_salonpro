from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Cliente
from app.schemas import ClienteCreate, ClienteResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(q: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Cliente)
    if q:
        query = query.filter(Cliente.nombre.ilike(f"%{q}%") | Cliente.apellido.ilike(f"%{q}%"))
    return query.all()

@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.post("/", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cliente = Cliente(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(cliente_id: int, cliente: ClienteCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for key, value in cliente.model_dump().items():
        setattr(db_cliente, key, value)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

@router.delete("/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(db_cliente)
    db.commit()
    return {"detail": "Cliente eliminado"}