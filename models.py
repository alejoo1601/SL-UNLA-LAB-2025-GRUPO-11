from sqlalchemy import Column,Integer,String,Date,Boolean
from database import engine,Base

class Persona(Base):
    __tablename__ = "personas"


    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String,unique=True, nullable=False)
    dni = Column(Integer, unique=True, nullable=False)
    telefono = Column(String,nullable=False)
    fecha_Nacimiento = Column(Date,nullable=False)
    edad = Column(Integer,nullable=False)
    habilitado= Column(Boolean,default=True)