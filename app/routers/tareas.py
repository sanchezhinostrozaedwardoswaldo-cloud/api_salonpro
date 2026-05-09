from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models import Tarea
from app.schemas import TareaCreate, TareaUpdate, TareaResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/tareas", tags=["Tareas"])

@router.get("/", response_model=List[TareaResponse])
def listar_tareas(
    estado: Optional[str] = None,
    asignado_a: Optional[int] = None,
    prioridad: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Tarea)
    if estado:
        query = query.filter(Tarea.estado == estado)
    if asignado_a:
        query = query.filter(Tarea.asignado_a == asignado_a)
    if prioridad:
        query = query.filter(Tarea.prioridad == prioridad)
    return query.all()

@router.post("/", response_model=TareaResponse)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_tarea = Tarea(**tarea.model_dump())
    db.add(db_tarea)
    db.commit()
    db.refresh(db_tarea)
    return db_tarea

@router.get("/{tarea_id}", response_model=TareaResponse)
def obtener_tarea(tarea_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea

@router.patch("/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(tarea_id: int, tarea: TareaUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    for key, value in tarea.model_dump(exclude_unset=True).items():
        setattr(db_tarea, key, value)
    db_tarea.actualizado_en = func.datetime('now', 'localtime')
    db.commit()
    db.refresh(db_tarea)
    return db_tarea

@router.delete("/{tarea_id}")
def eliminar_tarea(tarea_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(db_tarea)
    db.commit()
    return {"detail": "Tarea eliminada"}