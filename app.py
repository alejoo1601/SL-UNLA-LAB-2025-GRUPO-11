from datetime import date, timedelta
from typing import Optional, List, Dict
from sqlalchemy import func
import calendar

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from Modelos.models import Persona, Turno, EstadoTurno
from Esquemas.schemas import (
    PersonaIn, PersonaUpdate, PersonaOut,
    TurnoIn, TurnoUpdate, TurnoOut, TurnosDisponiblesOut,
)
from Utilidades.utils import (
    get_db, validar_email, parsear_hora,
    SLOTS_FIJOS, persona_por_dni_o_404, turno_o_404
)

app = FastAPI(title="TP Grupo 11", version="1.5")

# PERSONAS
# 1. 
@app.post("/personas", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(datos: PersonaIn, db: Session = Depends(get_db)):
    validar_email(datos.email)

    if db.query(Persona).filter(Persona.email == datos.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")

    if db.query(Persona).filter(Persona.dni == datos.dni).first():
        raise HTTPException(status_code=409, detail="DNI ya registrado")

    persona = Persona(
        nombre=datos.nombre,
        email=datos.email,
        dni=datos.dni,
        telefono=datos.telefono,
        fecha_Nacimiento=datos.fecha_Nacimiento,
        habilitado=datos.habilitado
    )

    db.add(persona)
    db.commit()
    db.refresh(persona)

    return {
        "nombre": persona.nombre,
        "email": persona.email,
        "dni": persona.dni,
        "telefono": persona.telefono,
        "fecha_Nacimiento": persona.fecha_Nacimiento,
        "habilitado": persona.habilitado,
        "edad": persona.edad
    }

# 2. 
@app.get("/personas", response_model=List[PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    personas = db.query(Persona).all()
    salida = []
    for p in personas:
        salida.append({
            "nombre": p.nombre,
            "email": p.email,
            "dni": p.dni,
            "telefono": p.telefono,
            "fecha_Nacimiento": p.fecha_Nacimiento,
            "habilitado": p.habilitado,
            "edad": p.edad
        })
    return salida

# 3. 
@app.get("/personas/{dni}", response_model=PersonaOut)
def obtener_persona(dni: int, db: Session = Depends(get_db)):
    p = persona_por_dni_o_404(db, dni)
    return {
        "nombre": p.nombre,
        "email": p.email,
        "dni": p.dni,
        "telefono": p.telefono,
        "fecha_Nacimiento": p.fecha_Nacimiento,
        "habilitado": p.habilitado,
        "edad": p.edad
    }

# 4. 
@app.put("/personas/{dni}", response_model=PersonaOut)
def actualizar_persona(dni: int, cambios: PersonaUpdate, db: Session = Depends(get_db)):
    p = persona_por_dni_o_404(db, dni)

    if cambios.nombre is not None:
        p.nombre = cambios.nombre

    if cambios.email is not None:
        validar_email(cambios.email)
        existe_otro = db.query(Persona).filter(
            Persona.email == cambios.email, Persona.id != p.id
        ).first()
        if existe_otro:
            raise HTTPException(status_code=409, detail="Email ya registrado por otra persona")
        p.email = cambios.email

    if cambios.telefono is not None:
        p.telefono = cambios.telefono

    if cambios.fecha_Nacimiento is not None:
        p.fecha_Nacimiento = cambios.fecha_Nacimiento

    if cambios.habilitado is not None:
        p.habilitado = cambios.habilitado

    db.commit()
    db.refresh(p)

    return {
        "nombre": p.nombre,
        "email": p.email,
        "dni": p.dni,
        "telefono": p.telefono,
        "fecha_Nacimiento": p.fecha_Nacimiento,
        "habilitado": p.habilitado,
        "edad": p.edad
    }

# 5. 
@app.delete("/personas/{dni}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_persona(dni: int, db: Session = Depends(get_db)):
    p = persona_por_dni_o_404(db, dni)
    db.delete(p)
    db.commit()
    return None

# TURNOS
# 6. 
@app.post("/turnos", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(datos: TurnoIn, db: Session = Depends(get_db)):
    persona = persona_por_dni_o_404(db, datos.persona_dni)
    if not persona.habilitado:
        raise HTTPException(status_code=422, detail="La persona no está habilitada")

    hace_6m = date.today() - timedelta(days=30 * 6)
    cant_cancelados = db.query(Turno).filter(
        Turno.persona_id == persona.id,
        Turno.estado == EstadoTurno.cancelado,
        Turno.fecha >= hace_6m
    ).count()
    if cant_cancelados >= 5:
        raise HTTPException(
            status_code=422,
            detail="La persona tiene 5 o más cancelaciones en los últimos 6 meses"
        )

    hora_ok = parsear_hora(datos.hora)

    ya_ocupado = db.query(Turno).filter(
        Turno.fecha == datos.fecha,
        Turno.hora == hora_ok,
        Turno.estado != EstadoTurno.cancelado
    ).first()
    if ya_ocupado:
        raise HTTPException(status_code=409, detail="Ese horario ya está ocupado")

    estado_final = datos.estado or EstadoTurno.pendiente
    turno = Turno(
        fecha=datos.fecha,
        hora=hora_ok,
        estado=estado_final,
        persona_id=persona.id
    )
    db.add(turno)
    db.commit()
    db.refresh(turno)

    return {
        "id": turno.id,
        "fecha": turno.fecha,
        "hora": turno.hora.strftime("%H:%M"),
        "estado": turno.estado,
        "persona_dni": persona.dni
    }

# 7. 
@app.get("/turnos", response_model=List[TurnoOut])
def listar_turnos(
    db: Session = Depends(get_db),
    persona_dni: Optional[int] = None,
    estado: Optional[EstadoTurno] = None,
    fecha: Optional[date] = None
):
    q = db.query(Turno)

    if persona_dni is not None:
        p = db.query(Persona).filter(Persona.dni == persona_dni).first()
        if not p:
            return []
        q = q.filter(Turno.persona_id == p.id)

    if estado is not None:
        q = q.filter(Turno.estado == estado)

    if fecha is not None:
        q = q.filter(Turno.fecha == fecha)

    salida = []
    for t in q.order_by(Turno.fecha.desc(), Turno.hora.desc()).all():
        salida.append({
            "id": t.id,
            "fecha": t.fecha,
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado,
            "persona_dni": t.persona.dni
        })
    return salida

# 8. 
@app.get("/turnos/{turno_id}", response_model=TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    t = turno_o_404(db, turno_id)
    return {
        "id": t.id,
        "fecha": t.fecha,
        "hora": t.hora.strftime("%H:%M"),
        "estado": t.estado,
        "persona_dni": t.persona.dni
    }

# 9. 
@app.put("/turnos/{turno_id}", response_model=TurnoOut)
def actualizar_turno(turno_id: int, cambios: TurnoUpdate, db: Session = Depends(get_db)):
    t = turno_o_404(db, turno_id)

    if t.estado in (EstadoTurno.asistido, EstadoTurno.cancelado):
        raise HTTPException(status_code=422, detail="No se puede modificar un turno asistido o cancelado")

    nueva_fecha = t.fecha
    if cambios.fecha is not None:
        nueva_fecha = cambios.fecha

    nueva_hora = t.hora
    if cambios.hora is not None:
        nueva_hora = parsear_hora(cambios.hora)

    if nueva_fecha != t.fecha or nueva_hora != t.hora:
        ya_ocupado = db.query(Turno).filter(
            Turno.fecha == nueva_fecha,
            Turno.hora == nueva_hora,
            Turno.id != turno_id,
            Turno.estado != EstadoTurno.cancelado
        ).first()
        if ya_ocupado:
            raise HTTPException(status_code=409, detail="Ese horario ya está ocupado")

    if cambios.persona_dni is not None:
        p = persona_por_dni_o_404(db, cambios.persona_dni)
        if not p.habilitado:
            raise HTTPException(status_code=422, detail="La persona no está habilitada")
        t.persona_id = p.id

    nuevo_estado = getattr(cambios, "estado", None)
    if nuevo_estado is not None:
        t.estado = nuevo_estado

    t.fecha = nueva_fecha
    t.hora = nueva_hora

    db.commit()
    db.refresh(t)

    return {
        "id": t.id,
        "fecha": t.fecha,
        "hora": t.hora.strftime("%H:%M"),
        "estado": t.estado,
        "persona_dni": t.persona.dni
    }

# 10. 
@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(turno_id: int, db: Session = Depends(get_db)):
    t = turno_o_404(db, turno_id)

    if t.estado == EstadoTurno.asistido:
        raise HTTPException(status_code=422, detail="No se puede eliminar un turno asistido")

    db.delete(t)
    db.commit()
    return None

# TURNOS DISPONIBLES
# 11. 
@app.get("/turnos-disponibles", response_model=TurnosDisponiblesOut)
def turnos_disponibles(fecha: date, db: Session = Depends(get_db)):
    todos = set(SLOTS_FIJOS)

    bloquean = db.query(Turno).filter(
        Turno.fecha == fecha,
        Turno.estado != EstadoTurno.cancelado
    ).all()

    ocupados = {t.hora.strftime("%H:%M") for t in bloquean}
    disponibles = sorted(todos - ocupados)

    return {
        "fecha": fecha.isoformat(),
        "horarios_disponibles": disponibles
    }

# GESTION DE ESTADO DE TURNO
# 12. 
@app.put("/turnos/{turno_id}/cancelar", response_model=TurnoOut)
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):
    t = turno_o_404(db, turno_id)

    if t.estado == EstadoTurno.asistido:
        raise HTTPException(status_code=422, detail="No se puede cancelar un turno asistido")

    if t.estado == EstadoTurno.cancelado:
        return {
            "id": t.id,
            "fecha": t.fecha,
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado,
            "persona_dni": t.persona.dni
        }

    t.estado = EstadoTurno.cancelado
    db.commit()
    db.refresh(t)

    return {
        "id": t.id,
        "fecha": t.fecha,
        "hora": t.hora.strftime("%H:%M"),
        "estado": t.estado,
        "persona_dni": t.persona.dni
    }

# REPORTES
# 14. 
@app.get("/reportes/turnos-por-fecha")
def reportes_turnos_por_fecha(fecha: date, db: Session = Depends(get_db)):
    turnos = db.query(Turno).filter(Turno.fecha == fecha).order_by(Turno.hora.asc()).all()
    resultado = []
    for t in turnos:
        resultado.append({
            "id": t.id,
            "fecha": t.fecha,
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado,
            "persona_dni": t.persona.dni,
            "persona_nombre": t.persona.nombre
        })
    return {"fecha": fecha.isoformat(), "turnos": resultado}

# 15. 
@app.get("/reportes/turnos-por-persona")
def reportes_turnos_por_persona(dni: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.dni == dni).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    turnos = (
        db.query(Turno)
        .filter(Turno.persona_id == persona.id)
        .order_by(Turno.fecha.desc(), Turno.hora.desc())
        .all()
    )

    resultado = []
    for t in turnos:
        resultado.append({
            "id": t.id,
            "fecha": t.fecha,
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado,
        })

    return {
        "persona": {"dni": persona.dni, "nombre": persona.nombre},
        "turnos": resultado
    }

# 16. 
@app.get("/reportes/turnos-cancelados-por-mes")
def reportes_cancelados_mes_actual(db: Session = Depends(get_db)):
    hoy = date.today()
    anio, mes = hoy.year, hoy.month
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])

    turnos = db.query(Turno).filter(
        Turno.estado == EstadoTurno.cancelado,
        Turno.fecha >= primer_dia,
        Turno.fecha <= ultimo_dia
    ).order_by(Turno.fecha.asc(), Turno.hora.asc()).all()

    detalle = []
    for t in turnos:
        detalle.append({
            "id": t.id,
            "persona_dni": t.persona.dni,
            "fecha": t.fecha,
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado
        })

    resumen = db.query(
        Turno.fecha,
        func.count(Turno.id)
    ).filter(
        Turno.estado == EstadoTurno.cancelado,
        Turno.fecha >= primer_dia,
        Turno.fecha <= ultimo_dia
    ).group_by(Turno.fecha).order_by(Turno.fecha.asc()).all()

    meses_es = ["", "enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]

    return {
        "anio": anio,
        "mes": meses_es[mes],
        "cantidad": len(detalle),
        "resumen_por_fecha": [{"fecha": f.isoformat(), "cantidad": c} for (f, c) in resumen],
        "turnos": detalle
    }
