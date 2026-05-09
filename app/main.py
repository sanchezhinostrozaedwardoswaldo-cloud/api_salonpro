from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, usuarios, clientes, citas, tareas
from app.database import Base, engine
from app import models

app = FastAPI(
    title="SalonPro Studio API",
    description="Sistema Web de Gestión Operativa para SalonPro Studio S.A.C.",
    version="1.0.0"
)


# CORS para permitir el frontend en GitHub Pages o local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(citas.router)
app.include_router(tareas.router)

@app.get("/")
def root():
    return {
        "message": "SalonPro Studio API v1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }