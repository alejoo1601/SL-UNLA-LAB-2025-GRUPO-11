import re
from datetime import date, datetime, timedelta, time as time_cls
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Persona, Turno, EstadoTurno

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -Validador de Mail
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validar_email(email: str):
    if not EMAIL_RE.match(email or ""):
        raise HTTPException(status_code=422, detail="Email inválido (use algo@dominio.com)")

# Constantes Horarios (09:00 a 16:30)
SLOT_START = time_cls(9, 0)   # 09:00
SLOT_END = time_cls(17, 0)    # 17:00 (último inicio válido: 16:30)
SLOT_STEP_MIN = 30

def _validar_slot(hora: time_cls):
    if hora.minute not in (0, 30) or hora.second != 0 or hora.microsecond != 0:
        raise HTTPException(status_code=422, detail="La hora debe ser cada 30' (HH:00 o HH:30).")
    ultimo_inicio = (datetime.combine(date.today(), SLOT_END) - timedelta(minutes=SLOT_STEP_MIN)).time()
    if not (SLOT_START <= hora <= ultimo_inicio):
        raise HTTPException(status_code=422, detail="Horario fuera de franja (09:00 a 16:30).")

def parsear_hora(hhmm: str) -> time_cls:
    try:
        hora = datetime.strptime(hhmm, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=422, detail="Hora inválida, use HH:MM (ej: 10:30)")
    _validar_slot(hora)
    return hora

def generar_slots_30min():
    """Genera ['09:00','09:30', ..., '16:30'] (una vez)."""
    slots = []
    h, m = SLOT_START.hour, SLOT_START.minute
    ultimo_inicio = (datetime.combine(date.today(), SLOT_END) - timedelta(minutes=SLOT_STEP_MIN)).time()
    while True:
        slots.append(f"{h:02d}:{m:02d}")
        m += SLOT_STEP_MIN
        if m >= 60:
            m -= 60
            h += 1
        if time_cls(h, m) > ultimo_inicio:
            break
    return tuple(slots)

SLOTS_FIJOS = set(generar_slots_30min()) 

def persona_por_dni_o_404(db: Session, dni: int) -> Persona:
    p = db.query(Persona).filter(Persona.dni == dni).first()
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

def turno_o_404(db: Session, turno_id: int) -> Turno:
    t = db.get(Turno, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t
