from sqlalchemy import Column, Integer, String, Date, Boolean, Time, Enum, ForeignKey, UniqueConstraint
from database import engine, Base
from datetime import date
import enum
#creacion tabla persona
class Persona(Base):
    __tablename__ = "personas"

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