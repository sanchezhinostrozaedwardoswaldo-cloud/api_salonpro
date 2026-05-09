from sqlalchemy import ForeignKey, Text, REAL, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from typing import Optional, List
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    rol: Mapped[str] = mapped_column(Text, nullable=False, default="empleado")
    activo: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    creado_en: Mapped[str] = mapped_column(Text, nullable=False, server_default=func.datetime('now', 'localtime'))

    citas: Mapped[List["Cita"]] = relationship(back_populates="usuario")
    tareas: Mapped[List["Tarea"]] = relationship(back_populates="asignado")


class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    apellido: Mapped[str] = mapped_column(Text, nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[str] = mapped_column(Text, nullable=False, server_default=func.datetime('now', 'localtime'))

    citas: Mapped[List["Cita"]] = relationship(back_populates="cliente")


class Cita(Base):
    __tablename__ = "citas"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    servicio: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[str] = mapped_column(Text, nullable=False)
    hora: Mapped[str] = mapped_column(Text, nullable=False)
    duracion_min: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default="pendiente")
    precio: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[str] = mapped_column(Text, nullable=False, server_default=func.datetime('now', 'localtime'))

    cliente: Mapped["Cliente"] = relationship(back_populates="citas")
    usuario: Mapped["Usuario"] = relationship(back_populates="citas")


class Tarea(Base):
    __tablename__ = "tareas"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asignado_a: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    prioridad: Mapped[str] = mapped_column(Text, nullable=False, default="media")
    estado: Mapped[str] = mapped_column(Text, nullable=False, default="pendiente")
    fecha_limite: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[str] = mapped_column(Text, nullable=False, server_default=func.datetime('now', 'localtime'))
    actualizado_en: Mapped[str] = mapped_column(Text, nullable=False, server_default=func.datetime('now', 'localtime'))

    asignado: Mapped[Optional["Usuario"]] = relationship(back_populates="tareas")