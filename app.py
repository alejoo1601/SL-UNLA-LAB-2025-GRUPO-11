from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import Persona
from datetime import date

app = FastAPI()

#crear tablas al iniciar
Base.metadata.create_all(bind=engine)

# Dependencia para manejar la sesión con la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        # Crear persona (POST)


@app.post("/personas/")
def crear_persona(
    nombre: str,
    email: str,
    dni: int,
    telefono: str,
    fecha_Nacimiento: date,
    db: Session = Depends(get_db),
):
    nueva = Persona(
        nombre=nombre,
        email=email,
        dni=dni,
        telefono=telefono,
        fecha_Nacimiento=fecha_Nacimiento,
        
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

# Listar todas las personas (GET)
@app.get("/personas/")
def listar_personas(db: Session = Depends(get_db)):
    return db.query(Persona).all()