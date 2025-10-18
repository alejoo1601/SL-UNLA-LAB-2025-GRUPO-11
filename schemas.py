from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field
from models import EstadoTurno

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
    hora: str
    estado: Optional[EstadoTurno] = EstadoTurno.pendiente
    persona_dni: int

class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[str] = None
    estado: Optional[EstadoTurno] = None 
    persona_dni: Optional[int] = None

class TurnoOut(BaseModel):
    id: int
    fecha: date
    hora: str
    estado: EstadoTurno
    persona_dni: int

class TurnosDisponiblesOut(BaseModel):
    fecha: str
    horarios_disponibles: List[str]
