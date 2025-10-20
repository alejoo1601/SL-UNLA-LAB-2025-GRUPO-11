from sqlalchemy import Column, Integer, String, Date, Boolean, Time, Enum, ForeignKey
from sqlalchemy.orm import relationship
from BaseDatos.database import engine, Base
from datetime import date
import enum

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
    pendiente = "pendiente"
    cancelado = "cancelado"
    confirmado = "confirmado"
    asistido = "asistido"

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
