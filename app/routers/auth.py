from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.schemas import LoginRequest, Token
from app.dependencies import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == credentials.email).first()

    print("Email ingresado:", credentials.email)
    print("Password ingresada:", credentials.password)
    print("Usuario encontrado:", user)

    if user:
        print("Hash en BD:", user.password)
        print("Resultado verify_password:",
            verify_password(credentials.password, user.password))

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}