from datetime import date, datetime
from typing import Optional, List
import re

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, Base, engine
from models import Persona, Turno

# crear tablas al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TP - Personas y Turnos", version="1.0.0")

# Dependencia para manejar la sesión con la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# validador del email
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Funciones auxiliares:
def validar_email(email: str):
    if not EMAIL_RE.match(email or ""):
        raise HTTPException(status_code=422, detail="Email inválido (formato)")

def parse_hora(hhmm: str):
    try:
        return datetime.strptime(hhmm, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=422, detail="Hora inválida, use HH:MM")

def get_persona_or_404(db: Session, dni: int) -> Persona:
    p = db.get(Persona, dni)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

#-----Clases-----
class PersonaIn(BaseModel):
    nombre: str = Field(min_length=1)
    email: str
    dni: int
    telefono: str
    fecha_Nacimiento: date
    habilitado: bool = True

class PersonaUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    fecha_Nacimiento: Optional[date] = None
    habilitado: Optional[bool] = None

class PersonaOut(PersonaIn):
    edad: int

# ABM Personas
# -----------------------------
@app.post("/personas", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(payload: PersonaIn, db: Session = Depends(get_db)):
    validar_email(payload.email)

    # email único
    if db.query(Persona).filter(Persona.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    # dni único (PK)
    if db.get(Persona, payload.dni):
        raise HTTPException(status_code=409, detail="DNI ya registrado")

    p = Persona(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)

    return {**payload.model_dump(), "edad": p.edad}

@app.get("/personas", response_model=List[PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    personas = db.query(Persona).all()
    return [{
        "nombre": p.nombre,
        "email": p.email,
        "dni": p.dni,
        "telefono": p.telefono,
        "fecha_Nacimiento": p.fecha_Nacimiento,
        "habilitado": p.habilitado,
        "edad": p.edad
    } for p in personas]

@app.get("/personas/{dni}", response_model=PersonaOut)
def obtener_persona(dni: int, db: Session = Depends(get_db)):
    p = get_persona_or_404(db, dni)
    return {
        "nombre": p.nombre,
        "email": p.email,
        "dni": p.dni,
        "telefono": p.telefono,
        "fecha_Nacimiento": p.fecha_Nacimiento,
        "habilitado": p.habilitado,
        "edad": p.edad
    }

@app.put("/personas/{dni}", response_model=PersonaOut)
def actualizar_persona(dni: int, payload: PersonaUpdate, db: Session = Depends(get_db)):
    p = get_persona_or_404(db, dni)
    data = payload.model_dump(exclude_unset=True)

    if "email" in data:
        validar_email(data["email"])
        existe = db.query(Persona).filter(Persona.email == data["email"], Persona.dni != dni).first()
        if existe:
            raise HTTPException(status_code=409, detail="Email ya registrado por otra persona")

    for k, v in data.items():
        setattr(p, k, v)

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