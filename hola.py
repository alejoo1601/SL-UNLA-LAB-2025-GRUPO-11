from fastapi import FastAPI

app = FastAPI()

@app.get("/hola_mundo")

def hola_mundo():
    return "Hello World!"

print ("hola grupo")
print ("q jodido es esto")