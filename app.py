from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
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

def get_persona_or_404(db: Session, dni: int) -> Persona:
    p = db.get(Persona, dni)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p
@app.post("/personas/")
def crear_persona(
    nombre: str,
    email: str,
    dni: int,
    telefono: str,
    fecha_nacimiento: date,
    db: Session = Depends(get_db),
):
    nueva = Persona(
        nombre=nombre,
        email=email,
        dni=dni,
        telefono=telefono,
        fecha_nacimiento=fecha_nacimiento,
        
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

# Listar todas las personas (GET)
@app.get("/personas/")
def listar_personas(db: Session = Depends(get_db)):
    return db.query(Persona).all()

@app.put("/personas/{dni}", response_model=PersonaOut)
def actualizar_persona(dni: int, payload: dict, db: Session = Depends(get_db)):
    p = db.query(Persona).filter(Persona.dni == dni).first()
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    # si cambian email, validar unicidad
    if "email" in payload:
        existe = db.query(Persona).filter(Persona.email == payload["email"], Persona.dni != dni).first()
        if existe:
            raise HTTPException(status_code=409, detail="Email ya registrado por otra persona")

    # Recorremos los datos recibidos y actualizamos los campos
    for key, value in payload.items():
        if hasattr(p, key):
            setattr(p, key, value)

    db.commit()
    db.refresh(p)
    return {
        "nombre": p.nombre,
        "email": p.email,
        "dni": p.dni,
        "telefono": p.telefono,
        "fecha_Nacimiento": p.fecha_Nacimiento,
        "habilitado": p.habilitado,
        "edad": p.edad
    }

@app.delete("/personas/{dni}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_persona(dni: int, db: Session = Depends(get_db)):
    p = get_persona_or_404(db, dni)
    db.delete(p)
    db.commit()
    return None