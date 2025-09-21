from datetime import date, datetime, timedelta
from datetime import time as time_cls
from typing import Optional, List, Dict
import re

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal, Base, engine
from models import Persona, Turno, EstadoTurno

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

def get_turno_or_404(db: Session, tid: int) -> Turno:
    t = db.get(Turno, tid)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

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

class TurnoIn(BaseModel):
    fecha: date
    hora: str                      # "HH:MM"
    estado: Optional[EstadoTurno] = EstadoTurno.pendiente
    persona_dni: int

class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[str] = None     # "HH:MM"
    estado: Optional[EstadoTurno] = None
    persona_dni: Optional[int] = None

class TurnoOut(BaseModel):
    id: int
    fecha: date
    hora: str
    estado: EstadoTurno
    persona_dni: int

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

# ABM Turnos
# -----------------------------
@app.post("/turnos", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(payload: TurnoIn, db: Session = Depends(get_db)):
    persona = get_persona_or_404(db, payload.persona_dni)
    if not persona.habilitado:
        raise HTTPException(status_code=422, detail="La persona no está habilitada")

    # bloquear si tiene >=5 cancelados en los últimos 6 meses
    seis_meses_atras = date.today() - timedelta(days=30*6)
    cancelados = db.query(func.count(Turno.id)).filter(
        Turno.persona_dni == payload.persona_dni,
        Turno.estado == EstadoTurno.cancelado,
        Turno.fecha >= seis_meses_atras
    ).scalar() or 0
    if cancelados >= 5:
        raise HTTPException(status_code=422, detail="La persona tiene 5 o más cancelaciones en los últimos 6 meses")

    # Evitar que vea doble de fecha y hora
    hora = parse_hora(payload.hora)
    choque = db.query(Turno).filter(Turno.fecha == payload.fecha, Turno.hora == hora).first()
    if choque:
        raise HTTPException(status_code=409, detail="Ese horario ya está ocupado")

    estado = payload.estado or EstadoTurno.pendiente
    t = Turno(fecha=payload.fecha, hora=hora, estado=estado, persona_dni=payload.persona_dni)
    db.add(t)
    db.commit()
    db.refresh(t)

    return {"id": t.id, "fecha": t.fecha, "hora": t.hora.strftime("%H:%M"), "estado": t.estado, "persona_dni": t.persona_dni}

@app.get("/turnos", response_model=List[TurnoOut])
def listar_turnos(db: Session = Depends(get_db),
                  persona_dni: Optional[int] = None,
                  estado: Optional[EstadoTurno] = None,
                  fecha: Optional[date] = None):
    q = db.query(Turno)
    if persona_dni is not None:
        q = q.filter(Turno.persona_dni == persona_dni)
    if estado is not None:
        q = q.filter(Turno.estado == estado)
    if fecha is not None:
        q = q.filter(Turno.fecha == fecha)

    res = []
    for t in q.order_by(Turno.fecha.desc(), Turno.hora.desc()).all():
        res.append({"id": t.id, "fecha": t.fecha, "hora": t.hora.strftime("%H:%M"),
                    "estado": t.estado, "persona_dni": t.persona_dni})
    return res

@app.get("/turnos/{id}", response_model=TurnoOut)
def obtener_turno(id: int, db: Session = Depends(get_db)):
    t = get_turno_or_404(db, id)
    return {"id": t.id, "fecha": t.fecha, "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado, "persona_dni": t.persona_dni}

@app.put("/turnos/{id}", response_model=TurnoOut)
def actualizar_turno(id: int, payload: TurnoUpdate, db: Session = Depends(get_db)):
    t = get_turno_or_404(db, id)
    data = payload.model_dump(exclude_unset=True)

    nueva_fecha = data.get("fecha", t.fecha)
    nueva_hora = parse_hora(data["hora"]) if "hora" in data else t.hora

    # Validar colision al cambiar fecha o hora
    if nueva_fecha != t.fecha or nueva_hora != t.hora:
        choque = db.query(Turno).filter(
            Turno.fecha == nueva_fecha,
            Turno.hora == nueva_hora,
            Turno.id != id
        ).first()
        if choque:
            raise HTTPException(status_code=409, detail="Ese horario ya está ocupado")

    # Reasignacion de persona
    if "persona_dni" in data:
        p = get_persona_or_404(db, data["persona_dni"])
        if not p.habilitado:
            raise HTTPException(status_code=422, detail="La persona no está habilitada")
        t.persona_dni = data["persona_dni"]

    # Confirma cambios
    t.fecha = nueva_fecha
    t.hora = nueva_hora
    if "estado" in data:
        t.estado = data["estado"]

    db.commit()
    db.refresh(t)
    return {"id": t.id, "fecha": t.fecha, "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado, "persona_dni": t.persona_dni}

@app.delete("/turnos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(id: int, db: Session = Depends(get_db)):
    t = get_turno_or_404(db, id)
    db.delete(t)
    db.commit()
    
def generar_slots_30min():
    
    #Genera los horarios desde 09:00 hasta 16:30 inclusive 
    slots = []
    h, m = 9, 0
    while True:
        slots.append(f"{h:02d}:{m:02d}")
        # suma 30 min
        m += 30
        if m == 60:
            m = 0
            h += 1
        # si el proximo inicio es 17:00, termina
        if h == 17 and m == 0:
            break
    return slots

@app.get("/turnos-disponibles")
def turnos_disponibles(fecha: date, db: Session = Depends(get_db)) -> Dict[str, object]:
    
    #Devuelve los horarios disponibles
    todos = set(generar_slots_30min())

    # ocupados = cualquiera que NO esté cancelado
    ocupados = db.query(Turno).filter(
        Turno.fecha == fecha,
        Turno.estado != EstadoTurno.cancelado
    ).all()

    no_disponibles = {t.hora.strftime("%H:%M") for t in ocupados}
    disponibles = sorted(todos - no_disponibles)

    return {
        "fecha": fecha.isoformat(),
        "horarios_disponibles": disponibles
    }
