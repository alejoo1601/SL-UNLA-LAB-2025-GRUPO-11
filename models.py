from sqlalchemy import Column,Integer,String,Date,Boolean
from database import engine,Base
from datetime import date

class Persona(Base):
    __tablename__ = "personas"


    dni = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String,unique=True, nullable=False)
    telefono = Column(String,nullable=False)
    fecha_Nacimiento = Column(Date,nullable=False)
    habilitado= Column(Boolean,default=True)

 # EDAD por fecha de nacimiento
    @property
    def edad(self):
        hoy = date.today()
        return hoy.year - self.fecha_Nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_Nacimiento.month, self.fecha_Nacimiento.day)
        )