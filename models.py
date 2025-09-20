from sqlalchemy import Column, Integer, String, Date, Boolean, Time, Enum, ForeignKey, UniqueConstraint
from database import engine, Base
from datetime import date
import enum
#creacion tabla persona
class Persona(Base):
    tablename = "personas"

    dni = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String, nullable=False)
    fecha_Nacimiento = Column(Date, nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)

#calculo de edad segun fecha de nacimiento
    @property
    def edad(self) -> int:
        hoy = date.today()
        return hoy.year - self.fecha_Nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_Nacimiento.month, self.fecha_Nacimiento.day)
        )

class EstadoTurno(str, enum.Enum):
    pendiente = "pendiente"
    cancelado = "cancelado"
    confirmado = "confirmado"
    asistido = "asistido"

class Turno(Base):
    tablename = "turnos"
    table_args = (
        UniqueConstraint("fecha", "hora", name="uq_turno_fecha_hora"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=False, index=True)
    estado = Column(Enum(EstadoTurno), nullable=False, default=EstadoTurno.pendiente)
    persona_dni = Column(Integer, ForeignKey("personas.dni", ondelete="CASCADE"), nullable=False, index=True)

#crea las tablas si no existen
Base.metadata.create_all(bind=engine)



    