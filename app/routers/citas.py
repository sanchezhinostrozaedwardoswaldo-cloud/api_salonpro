from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Cita
from app.schemas import CitaCreate, CitaUpdate, CitaResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/citas", tags=["Citas"])

@router.get("/", response_model=List[CitaResponse])
def listar_citas(
    fecha: Optional[str] = None,
    estado: Optional[str] = None,
    cliente_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Cita)
    if fecha:
        query = query.filter(Cita.fecha == fecha)
    if estado:
        query = query.filter(Cita.estado == estado)
    if cliente_id:
        query = query.filter(Cita.cliente_id == cliente_id)
    return query.all()

@router.post("/", response_model=CitaResponse)
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cita = Cita(**cita.model_dump())
    db.add(db_cita)
    db.commit()
    db.refresh(db_cita)
    return db_cita

@router.get("/{cita_id}", response_model=CitaResponse)
def obtener_cita(cita_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.patch("/{cita_id}", response_model=CitaResponse)
def actualizar_cita(cita_id: int, cita: CitaUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not db_cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    for key, value in cita.model_dump(exclude_unset=True).items():
        setattr(db_cita, key, value)
    db.commit()
    db.refresh(db_cita)
    return db_cita

@router.delete("/{cita_id}")
def eliminar_cita(cita_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not db_cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.delete(db_cita)
    db.commit()
    return {"detail": "Cita eliminada"}