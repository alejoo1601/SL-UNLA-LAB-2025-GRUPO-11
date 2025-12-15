from sqlalchemy import Column, Integer, String, Date, Boolean, Time, Enum, ForeignKey
from sqlalchemy.orm import relationship
from BaseDatos.database import engine, Base
from datetime import date
import enum
import os
from dotenv import load_dotenv

load_dotenv()

ESTADO_TURNO_PENDIENTE: str = os.getenv("ESTADO_TURNO_PENDIENTE")
ESTADO_TURNO_ASISTIDO: str = os.getenv("ESTADO_TURNO_ASISTIDO")
ESTADO_TURNO_CONFIRMADO: str = os.getenv("ESTADO_TURNO_CONFIRMADO")
ESTADO_TURNO_CANCELADO: str = os.getenv("ESTADO_TURNO_CANCELADO")

class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)  
    dni = Column(Integer, unique=True, nullable=False, index=True)        
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String, nullable=False)
    fecha_Nacimiento = Column(Date, nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)

    # relación 1→N: una persona tiene muchos turnos
    turnos = relationship("Turno", back_populates="persona", cascade="all, delete")

    @property
    def edad(self) -> int:
        hoy = date.today()
        edad = hoy.year - self.fecha_Nacimiento.year
        if hoy.month < self.fecha_Nacimiento.month:
            edad -= 1
        elif hoy.month == self.fecha_Nacimiento.month and hoy.day < self.fecha_Nacimiento.day:
            edad -= 1
        return edad

class EstadoTurno(str, enum.Enum):
    pendiente = ESTADO_TURNO_PENDIENTE
    cancelado = ESTADO_TURNO_ASISTIDO
    confirmado = ESTADO_TURNO_CONFIRMADO
    asistido = ESTADO_TURNO_CANCELADO

class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=False, index=True)
    estado = Column(Enum(EstadoTurno), nullable=False, default=EstadoTurno.pendiente)
    persona_id = Column(Integer, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)

    # relación N→1: cada turno pertenece a una persona
    persona = relationship("Persona", back_populates="turnos")

# crea las tablas si no existen
Base.metadata.create_all(bind=engine)
