from fastapi import FastAPI
from database import engine, Base
import models

app = FastAPI()

#crear tablas al iniciar
Base.metadata.create_all(bind=engine)

@app.get("/hola_mundo")

def hola_mundo():
    return "Hello World!"

