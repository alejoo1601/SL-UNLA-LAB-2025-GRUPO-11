from datetime import date, timedelta
from typing import Optional, List
from sqlalchemy import func

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from Modelos.models import Persona, Turno, EstadoTurno

from Esquemas.schemas import (PersonaIn, PersonaUpdate, PersonaOut,
TurnoIn, TurnoUpdate, TurnoOut, TurnosDisponiblesOut,)

from Utilidades.utils import (get_db, validar_email, parsear_hora,SLOTS_FIJOS)

import os #habilita la libreria del SO.
import pandas as pd #Importo Pandas como "pd".
from fastapi.responses import FileResponse #"Permite descargar el archivo en el buscador web con fastapi".
from Utilidades.utils import escribir_lineas_en_pdf #Importo la funcion de utils.py.

app = FastAPI(title="TP Grupo 11", version="1.8.1")

# PERSONAS
# 1.
@app.post("/personas", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(datos: PersonaIn, db: Session = Depends(get_db)):
    try:
        try:
            validar_email(datos.email)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error validando email: {e}")

        try:
            existe_email = db.query(Persona).filter(Persona.email == datos.email).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando email: {e}")
        if existe_email:
            raise HTTPException(status_code=409, detail="Email ya registrado")

        try:
            existe_dni = db.query(Persona).filter(Persona.dni == datos.dni).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando DNI: {e}")
        if existe_dni:
            raise HTTPException(status_code=409, detail="DNI ya registrado")

        try:
            p = Persona(
                nombre=datos.nombre,
                email=datos.email,
                dni=datos.dni,
                telefono=datos.telefono,
                fecha_Nacimiento=datos.fecha_Nacimiento,
                habilitado=datos.habilitado
            )
            db.add(p)
            db.commit()
            db.refresh(p)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error guardando persona: {e}")

        return PersonaOut(
            nombre=p.nombre, email=p.email, dni=p.dni, telefono=p.telefono,
            fecha_Nacimiento=p.fecha_Nacimiento, habilitado=p.habilitado, edad=p.edad
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 2.
@app.get("/personas", response_model=List[PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    try:
        try:
            personas = db.query(Persona).order_by(Persona.id.asc()).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando personas: {e}")

        salida: List[PersonaOut] = []
        for p in personas:
            try:
                edad = p.edad
            except Exception:
                edad = None
            salida.append(
                PersonaOut(
                    nombre=p.nombre, email=p.email, dni=p.dni, telefono=p.telefono,
                    fecha_Nacimiento=p.fecha_Nacimiento, habilitado=p.habilitado, edad=edad
                )
            )
        return salida

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 3.
@app.get("/personas/{dni}", response_model=PersonaOut)
def obtener_persona(dni: int, db: Session = Depends(get_db)):
    try:
        try:
            p = db.query(Persona).filter(Persona.dni == dni).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        try:
            edad = p.edad
        except Exception:
            edad = None

        return PersonaOut(
            nombre=p.nombre, email=p.email, dni=p.dni, telefono=p.telefono,
            fecha_Nacimiento=p.fecha_Nacimiento, habilitado=p.habilitado, edad=edad
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 4.
@app.put("/personas/{dni}", response_model=PersonaOut)
def actualizar_persona(dni: int, cambios: PersonaUpdate, db: Session = Depends(get_db)):
    try:
        try:
            p = db.query(Persona).filter(Persona.dni == dni).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        if cambios.nombre is not None:
            p.nombre = cambios.nombre

        if cambios.email is not None:
            try:
                validar_email(cambios.email)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error validando email: {e}")

            try:
                existe_otro = db.query(Persona).filter(
                    Persona.email == cambios.email, Persona.id != p.id
                ).first()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error verificando email único: {e}")
            if existe_otro:
                raise HTTPException(status_code=409, detail="Email ya registrado por otra persona")
            p.email = cambios.email

        if cambios.telefono is not None:
            p.telefono = cambios.telefono

        if cambios.fecha_Nacimiento is not None:
            p.fecha_Nacimiento = cambios.fecha_Nacimiento

        if cambios.habilitado is not None:
            p.habilitado = cambios.habilitado

        try:
            db.commit()
            db.refresh(p)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error actualizando persona: {e}")

        return PersonaOut(
            nombre=p.nombre, email=p.email, dni=p.dni, telefono=p.telefono,
            fecha_Nacimiento=p.fecha_Nacimiento, habilitado=p.habilitado, edad=p.edad
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 5.
@app.delete("/personas/{dni}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_persona(dni: int, db: Session = Depends(get_db)):
    try:
        try:
            p = db.query(Persona).filter(Persona.dni == dni).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        try:
            db.delete(p)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error eliminando persona: {e}")

        return None

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# TURNOS
# 6.
@app.post("/turnos", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(datos: TurnoIn, db: Session = Depends(get_db)):
    try:
        try:
            persona = db.query(Persona).filter(Persona.dni == datos.persona_dni).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
        if not persona:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        if not persona.habilitado:
            raise HTTPException(status_code=422, detail="La persona no está habilitada")

        hace_6m = date.today() - timedelta(days=180)
        try:
            cancelados = db.query(Turno).filter(
                Turno.persona_id == persona.id,
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= hace_6m
            ).count()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error verificando cancelaciones: {e}")
        if cancelados >= 5:
            raise HTTPException(status_code=422, detail="≥5 cancelados en los últimos 6 meses")

        try:
            hora_ok = parsear_hora(datos.hora)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parseando hora: {e}")

        try:
            colision = db.query(Turno).filter(
                Turno.fecha == datos.fecha,
                Turno.hora == hora_ok,
                Turno.estado != EstadoTurno.cancelado
            ).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error comprobando colisión: {e}")
        if colision:
            raise HTTPException(status_code=409, detail="Horario ocupado")

        try:
            t = Turno(
                fecha=datos.fecha,
                hora=hora_ok,
                estado=datos.estado or EstadoTurno.pendiente,
                persona_id=persona.id
            )
            db.add(t)
            db.commit()
            db.refresh(t)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error guardando turno: {e}")

        return TurnoOut(
            id=t.id, fecha=t.fecha, hora=t.hora.strftime("%H:%M"),
            estado=t.estado, persona_dni=persona.dni
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 7.
@app.get("/turnos", response_model=List[TurnoOut])
def listar_turnos(persona_dni: Optional[int] = None,estado: Optional[EstadoTurno] = None,
                  fecha: Optional[date] = None,db: Session = Depends(get_db),):
    try:
        try:
            q = db.query(Turno)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creando consulta: {e}")

        if persona_dni is not None:
            try:
                persona = db.query(Persona).filter(Persona.dni == persona_dni).first()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
            if not persona:
                return []
            q = q.filter(Turno.persona_id == persona.id)

        if estado is not None:
            q = q.filter(Turno.estado == estado)

        if fecha is not None:
            q = q.filter(Turno.fecha == fecha)

        try:
            turnos = q.order_by(Turno.fecha.asc(), Turno.hora.asc()).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error leyendo turnos: {e}")

        salida: List[TurnoOut] = []
        for t in turnos:
            salida.append(
                TurnoOut(
                    id=t.id, fecha=t.fecha, hora=t.hora.strftime("%H:%M"),
                    estado=t.estado, persona_dni=t.persona.dni
                )
            )
        return salida

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 8.
@app.get("/turnos/{turno_id}", response_model=TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        try:
            t = db.get(Turno, turno_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turno: {e}")
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        return TurnoOut(
            id=t.id, fecha=t.fecha, hora=t.hora.strftime("%H:%M"),
            estado=t.estado, persona_dni=t.persona.dni
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 9.
@app.put("/turnos/{turno_id}", response_model=TurnoOut)
def actualizar_turno(turno_id: int, cambios: TurnoUpdate, db: Session = Depends(get_db)):
    try:
        try:
            t = db.get(Turno, turno_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turno: {e}")
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado in (EstadoTurno.asistido, EstadoTurno.cancelado):
            raise HTTPException(status_code=422, detail="No se puede editar un turno asistido o cancelado")

        nueva_fecha = t.fecha if cambios.fecha is None else cambios.fecha
        nueva_hora = t.hora
        if cambios.hora is not None:
            try:
                nueva_hora = parsear_hora(cambios.hora)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error parseando hora: {e}")

        if nueva_fecha != t.fecha or nueva_hora != t.hora:
            try:
                colision = db.query(Turno).filter(
                    Turno.id != t.id,
                    Turno.fecha == nueva_fecha,
                    Turno.hora == nueva_hora,
                    Turno.estado != EstadoTurno.cancelado
                ).first()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error comprobando colisión: {e}")
            if colision:
                raise HTTPException(status_code=409, detail="Horario ocupado")

        if cambios.persona_dni is not None:
            try:
                p = db.query(Persona).filter(Persona.dni == cambios.persona_dni).first()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error consultando persona destino: {e}")
            if not p:
                raise HTTPException(status_code=404, detail="Persona destino no encontrada")
            if not p.habilitado:
                raise HTTPException(status_code=422, detail="La persona destino no está habilitada")
            t.persona_id = p.id

        t.fecha = nueva_fecha
        t.hora = nueva_hora

        try:
            nuevo_estado = getattr(cambios, "estado", None)
        except Exception:
            nuevo_estado = None
        if nuevo_estado is not None:
            t.estado = nuevo_estado

        try:
            db.commit()
            db.refresh(t)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error actualizando turno: {e}")

        return TurnoOut(
            id=t.id, fecha=t.fecha, hora=t.hora.strftime("%H:%M"),
            estado=t.estado, persona_dni=t.persona.dni
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 10.
@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        try:
            t = db.get(Turno, turno_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turno: {e}")
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado == EstadoTurno.asistido:
            raise HTTPException(status_code=422, detail="No se puede eliminar un turno asistido")

        try:
            db.delete(t)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error eliminando turno: {e}")

        return None

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")



# DISPONIBILIDAD
# 11.
@app.get("/turnos-disponibles", response_model=TurnosDisponiblesOut)
def turnos_disponibles(fecha: date, db: Session = Depends(get_db)):
    try:
        todos = set(SLOTS_FIJOS)

        try:
            bloquean = db.query(Turno).filter(
                Turno.fecha == fecha,
                Turno.estado != EstadoTurno.cancelado
            ).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando ocupados: {e}")

        try:
            ocupados = {t.hora.strftime("%H:%M") for t in bloquean}
            disponibles = sorted(todos - ocupados)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculando disponibilidad: {e}")

        return {"fecha": fecha.isoformat(), "horarios_disponibles": disponibles}

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# GESTIÓN DE ESTADO
# 12.
@app.put("/turnos/{turno_id}/cancelar", response_model=TurnoOut)
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        try:
            t = db.get(Turno, turno_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turno: {e}")
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado == EstadoTurno.asistido:
            raise HTTPException(status_code=422, detail="No se puede cancelar un turno asistido")

        try:
            t.estado = EstadoTurno.cancelado
            db.commit()
            db.refresh(t)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error actualizando estado: {e}")

        return TurnoOut(
            id=t.id, fecha=t.fecha, hora=t.hora.strftime("%H:%M"),
            estado=t.estado, persona_dni=t.persona.dni
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 13.
@app.put("/turnos/{turno_id}/confirmar", response_model=TurnoOut)
def confirmar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        try:
            t = db.get(Turno, turno_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turno: {e}")
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado in (EstadoTurno.asistido, EstadoTurno.cancelado):
            raise HTTPException(status_code=422, detail="No se puede confirmar un turno asistido o cancelado")

        try:
            t.estado = EstadoTurno.confirmado
            db.commit()
            db.refresh(t)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error actualizando estado: {e}")

        return TurnoOut(
            id=t.id, fecha=t.fecha, hora=t.hora.strftime("%H:%M"),
            estado=t.estado, persona_dni=t.persona.dni
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")



# REPORTES
# 14.
@app.get("/reportes/turnos-por-fecha")
def reportes_turnos_por_fecha(fecha: date,db: Session = Depends(get_db)):
    try:
        try:
            turnos = (
                db.query(Turno)
                .join(Persona)
                .filter(Turno.fecha == fecha)
                .order_by(Persona.nombre.asc(), Turno.hora.asc())
                .all()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}")

        try:
            personas = []
            persona_actual = None
            lista_actual = None
            for t in turnos:
                clave = (t.persona.dni, t.persona.nombre)
                if persona_actual != clave:
                    persona_actual = clave
                    lista_actual = []
                    personas.append({"dni": clave[0], "nombre": clave[1], "turnos": lista_actual})
                lista_actual.append({
                    "id": t.id, "hora": t.hora.strftime("%H:%M"), "estado": t.estado
                })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error agrupando: {e}")

        return {"fecha": fecha.isoformat(), "personas": personas}

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 15.
@app.get("/reportes/turnos-por-persona")
def reportes_turnos_por_persona(dni: int, db: Session = Depends(get_db)):
    try:
        try:
            persona = db.query(Persona).filter(Persona.dni == dni).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
        if not persona:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        try:
            turnos = (
                db.query(Turno)
                .filter(Turno.persona_id == persona.id)
                .order_by(Turno.fecha.desc(), Turno.hora.desc())
                .all()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}")

        try:
            resultado = []
            for t in turnos:
                resultado.append({
                    "id": t.id,
                    "fecha": t.fecha,
                    "hora": t.hora.strftime("%H:%M"),
                    "estado": t.estado,
                })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error armando respuesta: {e}")

        return {"persona": {"dni": persona.dni, "nombre": persona.nombre}, "turnos": resultado}

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 16.
@app.get("/reportes/turnos-cancelados-por-mes")
def reportes_cancelados_mes(db: Session = Depends(get_db)):
    try:
        hoy = date.today()
        primero_mes = hoy.replace(day=1)
        primero_mes_sig = date(
            hoy.year + (1 if hoy.month == 12 else 0),
            1 if hoy.month == 12 else hoy.month + 1,
            1
        )

        try:
            turnos = (
                db.query(Turno)
                .filter(
                    Turno.estado == EstadoTurno.cancelado,
                    Turno.fecha >= primero_mes,
                    Turno.fecha < primero_mes_sig,
                )
                .order_by(Turno.fecha.asc(), Turno.hora.asc())
                .all()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando cancelados: {e}")

        try:
            resumen_rows = (
                db.query(Turno.fecha, func.count(Turno.id))
                .filter(
                    Turno.estado == EstadoTurno.cancelado,
                    Turno.fecha >= primero_mes,
                    Turno.fecha < primero_mes_sig,
                )
                .group_by(Turno.fecha)
                .order_by(Turno.fecha.asc())
                .all()
            )
            resumen = [{"fecha": f, "cantidad": c} for (f, c) in resumen_rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculando resumen: {e}")

        MESES = [
            "",
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        mes = MESES[hoy.month]

        return {
            "anio": hoy.year,
            "mes": mes,
            "cantidad": len(turnos),
            "resumen_por_fecha": resumen,
            "turnos": [
                {
                    "id": t.id,
                    "persona_dni": t.persona.dni,
                    "fecha": t.fecha,
                    "hora": t.hora.strftime("%H:%M"),
                    "estado": t.estado
                }
                for t in turnos
            ],
        }

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 17.
@app.get("/reportes/turnos-cancelados")
def reportes_personas_con_cancelados(min: int = 5, db: Session = Depends(get_db)):
    try:
        try:
            rows = (
                db.query(Turno.persona_id, func.count(Turno.id))
                .filter(Turno.estado == EstadoTurno.cancelado)
                .group_by(Turno.persona_id)
                .having(func.count(Turno.id) >= min)
                .all()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error agrupando cancelados: {e}")

        salida = []
        for persona_id, cant in rows:
            try:
                p = db.query(Persona).filter(Persona.id == persona_id).first()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}")
            try:
                t_list = (
                    db.query(Turno)
                    .filter(Turno.persona_id == persona_id, Turno.estado == EstadoTurno.cancelado)
                    .order_by(Turno.fecha.desc(), Turno.hora.desc())
                    .all()
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}")

            salida.append({
                "persona": {"dni": p.dni, "nombre": p.nombre},
                "cancelados": cant,
                "turnos": [
                    {"id": t.id, "fecha": t.fecha, "hora": t.hora.strftime("%H:%M"), "estado": t.estado}
                    for t in t_list
                ],
            })

        return {"min_cancelados": min, "personas": salida}

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 18.
@app.get("/reportes/turnos-confirmados")
def reportes_turnos_confirmados(desde: date, hasta: date, tamaño: int,pagina: int,
     db: Session = Depends(get_db)):
    try:
        if desde > hasta:
            raise HTTPException(status_code=400, detail="Rango inválido: 'desde' debe ser ≤ 'hasta'")

        if pagina < 1:
            pagina = 1

        try:
            q = db.query(Turno).filter(
                Turno.estado == EstadoTurno.confirmado,
                Turno.fecha >= desde,
                Turno.fecha <= hasta
            ).order_by(Turno.fecha.asc(), Turno.hora.asc())
            total = q.count()
            items = q.offset((pagina - 1) * tamaño).limit(tamaño).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando confirmados: {e}")

        try:
            salida = [
                {"id": t.id, "fecha": t.fecha, "hora": t.hora.strftime("%H:%M"), "persona_dni": t.persona.dni}
                for t in items
            ]
            total_paginas = (total + tamaño - 1) // tamaño
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error armando respuesta: {e}")

        return {
            "desde": desde.isoformat(), "hasta": hasta.isoformat(),
            "pagina": pagina, "tamaño": tamaño,
            "total": total, "Total Paginas": total_paginas,
            "items": salida,
        }

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 19.
@app.get("/reportes/estado-personas")
def reportes_estado_personas(habilitada: bool, db: Session = Depends(get_db)):
    try:
        try:
            personas = (
                db.query(Persona)
                .filter(Persona.habilitado == habilitada)
                .order_by(Persona.id.asc())
                .all()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando personas: {e}")

        try:
            salida = [
                {
                    "dni": p.dni, "nombre": p.nombre, "email": p.email,
                    "telefono": p.telefono, "habilitado": p.habilitado
                } for p in personas
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error armando respuesta: {e}")

        return {"habilitada": habilitada, "personas": salida}

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Reportes CSV
# 20.
@app.get("/reportes/turnos-por-persona-csv")
def turnos_por_persona_csv(dni: int, db: Session = Depends(get_db)): #Se pide el parametro del DNI y para tener una sesión de base de datos.
    try:
        try:
            persona = db.query(Persona).filter(Persona.dni == dni).first() #Busca si la persona segun el dni.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}") #si ocurre una excepcion tira el codigo 500.

        if not persona:
            raise HTTPException(status_code=404, detail="Persona no encontrada") #si no se encuentra se tira el codigo 404.

        try:
            turnos = (
                db.query(Turno)
                .filter(Turno.persona_id == persona.id)
                .order_by(Turno.fecha.desc(), Turno.hora.desc())
                .all()
            ) #Se busca los turnos del dni asignado, y se los ordena de manera decendente segun fecha y hora. Se almacena en turnos.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}") # si ocurre una excepcion se tira el codigo 500.

        filas = []
        for t in turnos:
            filas.append({
                "id": t.id,
                "fecha": t.fecha.isoformat(),
                "hora": t.hora.strftime("%H:%M"),
                "estado": t.estado.value,
            }) #Se muestra en un array (filas) con los turnos siguiendo el formato asignado en este bucle for.

        df = pd.DataFrame(filas) #Se define df como el dataframe de filas.

        os.makedirs("CSV", exist_ok=True) #Crea una carpeta "CSV" Si no existe en el directorio.
        archivo = os.path.join("CSV", f"turnos_{persona.nombre}.csv") #Crea el archivo .csv y se guarda en la carptea "CSV".
        df.to_csv(archivo, sep=";", index=False) #Se establece que el separador de datos sea el ";" usando la funcion del dataframe (.to_csv).

        return FileResponse(archivo, media_type="text/csv", filename=f"turnos_{persona.nombre}.csv") #Se descarga el archivo en el buscador web
    except HTTPException:
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.


# 21.
@app.get("/reportes/turnos-por-fecha-csv")
def turnos_por_fecha_csv(fecha: date, db: Session = Depends(get_db)): #Se pide el parametro de la fecha y para tener una sesión de base de datos.
    try:
        try:
            turnos = (
                db.query(Turno)
                .join(Persona)
                .filter(Turno.fecha == fecha)
                .order_by(Persona.nombre.asc(), Turno.hora.asc())
                .all()
            ) #Se busca los turnos, y se los ordena de manera ascendente segun la fecha asignada. Se almacena en turnos.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}") #Se tira una excepcion si hay un error con codigo 500.

        filas = []
        for t in turnos:
            filas.append({
                "dni_persona": t.persona.dni,
                "nombre": t.persona.nombre,
                "id_turno": t.id,
                "hora": t.hora.strftime("%H:%M"),
                "estado": t.estado.value,
            }) #Se muestra en un array (filas) con los turnos siguiendo el formato asignado en este bucle for.

        df = pd.DataFrame(filas) #Se define df como el dataframe de filas.
 
        os.makedirs("CSV", exist_ok=True) #Crea una carpeta "CSV" Si no existe en el directorio.
        archivo = os.path.join("CSV", f"turnos_{fecha.day}-{fecha.month}-{fecha.year}.csv") #Crea el archivo .csv y se guarda en la carptea "CSV".
        df.to_csv(archivo, sep=";", index=False) #Se establece que el separador de datos sea el ";" usando la funcion del dataframe (.to_csv).

        return FileResponse(archivo, media_type="text/csv", filename=f"turnos_{fecha.day}-{fecha.month}-{fecha.year}.csv") #Se descarga el archivo en el buscador web
    except HTTPException:
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.


# 22.
@app.get("/reportes/turnos-cancelados-mes-actual-csv") 
def turnos_cancelados_mes_actual_csv(db: Session = Depends(get_db)): #Se pide una sesión de base de datos.
    try:
        hoy = date.today() #Se obtiene la fecha actual.
        inicio = hoy.replace(day=1) #primer día del mes actual.
        fin = inicio.replace(month=inicio.month + 1) if inicio.month < 12 else inicio.replace(
            year=inicio.year + 1, month=1
        ) #Primer día del mes siguiente. Si el mes es de 1 a 11 sumamos 1 al mes sino si es diciembre (12) pasamos a enero del año siguiente.

        try:
            turnos = (
                db.query(Turno)
                .filter(
                    Turno.estado == EstadoTurno.cancelado,
                    Turno.fecha >= inicio,
                    Turno.fecha < fin
                )
                .order_by(Turno.fecha.asc(), Turno.hora.asc())
                .all()
            ) #Se busca los turnos dentro del rango de dias del mes que sean cancelados y de manera ascendente en fecha y hora.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}") #Se tira una excepcion si hay un error con codigo 500.

        filas = []
        for t in turnos:
            filas.append({
                "id": t.id,
                "dni_persona": t.persona.dni,
                "fecha": t.fecha.isoformat(),
                "hora": t.hora.strftime("%H:%M"),
            }) #Se muestra en un array (filas) con los turnos siguiendo el formato asignado en este bucle for.

        df = pd.DataFrame(filas) #Se define df como el dataframe de filas.

        os.makedirs("CSV", exist_ok=True) #Crea una carpeta "CSV" Si no existe en el directorio.
        archivo = os.path.join("CSV", "turnos_cancelados_mes_actual.csv") #Crea el archivo .csv y se guarda en la carptea "CSV".
        df.to_csv(archivo, sep=";", index=False) #Se establece que el separador de datos sea el ";" usando la funcion del dataframe (.to_csv).

        return FileResponse(archivo, media_type="text/csv", filename="turnos_cancelados_mes_actual.csv") #Se descarga el archivo en el buscador web
    except HTTPException: 
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.


# 23.
@app.get("/reportes/estado-personas-habilitadas-csv") 
def estado_personas_habilitadas_csv(habilitada: bool, db: Session = Depends(get_db)): #Se pide de parametro "habilitada" un booleano y una sesión de base de datos.
    
    if habilitada is False:
        raise HTTPException(status_code=400, detail="Debe ser 'True' el valor de 'habilitada'") #Se tira una excepcion 400 ya que habilitada es "false".

    try:
        try:
            personas = (
                db.query(Persona)
                .filter(Persona.habilitado == habilitada)
                .order_by(Persona.id.asc())
                .all()
            ) #Se busca las personas habilitadas y se ordenan de manera ascendente.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando personas: {e}") #Se tira una excepcion si hay un error con codigo 500.

        filas = []
        for p in personas:
            filas.append({
                "dni": p.dni,
                "nombre": p.nombre,
                "email": p.email,
                "telefono": p.telefono,
                "habilitado": p.habilitado,
            }) #Se muestra en un array (filas) con las personas siguiendo el formato asignado en este bucle for.

        df = pd.DataFrame(filas) #Se define df como el dataframe de filas.

        os.makedirs("CSV", exist_ok=True) #Crea una carpeta "CSV" Si no existe en el directorio.
        archivo = os.path.join("CSV", "estado_personas_habilitadas.csv") #Crea el archivo .csv y se guarda en la carptea "CSV".
        df.to_csv(archivo, sep=";", index=False) #Se establece que el separador de datos sea el ";" usando la funcion del dataframe (.to_csv).

        return FileResponse(archivo, media_type="text/csv", filename="estado_personas_habilitadas.csv") #Se descarga el archivo en el buscador web
    except HTTPException:
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.
    


#Reportes PDF
# 24.
@app.get("/reportes/turnos-por-persona-pdf") 
def turnos_por_persona_pdf(dni: int, db: Session = Depends(get_db)): #Se pide el parametro del DNI y para tener una sesión de base de datos.
    try:
      
        try:
            persona = db.query(Persona).filter(Persona.dni == dni).first() #Se busca la persona segun el DNI asignado.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando persona: {e}") #Se tira una excepcion si hay un error con codigo 500.

        if not persona:
            raise HTTPException(status_code=404, detail="Persona no encontrada") #Se tira una excepcion 404 porque no se encontro a la persona del DNI.

        try:
            turnos = (
                db.query(Turno)
                .filter(Turno.persona_id == persona.id)
                .order_by(Turno.fecha.desc(), Turno.hora.desc())
                .all()
            ) #Busca los turnos de esta persona por su id y los ordena de forma descendente en turnos.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}") #Se tira una excepcion si hay un error con codigo 500.

       
        titulo = f"{persona.nombre} DNI: {persona.dni}" #Se crea un titulo que indica a la persona que se le pide sus turnos.
        columnas = ["ID", "Fecha", "Hora", "Estado"] #El encabezado con la informacion a mostrar.

        filas = [] #Se crea las filas.

        filas.append([titulo, "", "", ""]) #Se agrega a las filas el titulo creado.

        for t in turnos:
            filas.append([
                t.id,
                t.fecha,
                t.hora.strftime("%H:%M"),
                t.estado.value,
            ]) #Se muestra en un array (filas) con los turnos siguiendo el formato asignado en este bucle for.

        os.makedirs("PDF", exist_ok=True) #Crea una carpeta "PDF" Si no existe en el directorio.
        archivo = os.path.join("PDF", f"turnos_{persona.nombre}.pdf") #Crea el archivo .pdf y se guarda en la carptea "PDF".
        escribir_lineas_en_pdf(columnas, filas, archivo) #Se envia a la funcion que esta en utils.py, la lista de columnas y filas, ademas de la ruta del archivo creado.

        return FileResponse(archivo, media_type="application/pdf", filename=f"turnos_{persona.nombre}.pdf") #Se descarga el archivo en el buscador web
    except HTTPException: 
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.


# 25.
@app.get("/reportes/turnos-por-fecha-pdf") 
def turnos_por_fecha_pdf(fecha: date, db: Session = Depends(get_db)): #Se pide el parametro de la fecha y para tener una sesión de base de datos.
    try:
        try:
            turnos = (
                db.query(Turno)
                .join(Persona)
                .filter(Turno.fecha == fecha)
                .order_by(Persona.nombre.asc(), Turno.hora.asc())
                .all() 
            ) #Se busca los turnos, y se los ordena de manera ascendente segun la fecha asignada. Se almacena en turnos.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}") #Se tira una excepcion si hay un error con codigo 500.

        columnas = ["DNI", "Nombre", "ID Turno", "Hora", "Estado"] #Se crea el encabezado.
        filas = [] #Se crea el array de filas.

        for t in turnos:
            filas.append([
                t.persona.dni,
                t.persona.nombre,
                t.id,
                t.hora.strftime("%H:%M"),
                t.estado.value,
            ]) #Se muestra en un array (filas) con los turnos siguiendo el formato asignado en este bucle for.

        os.makedirs("PDF", exist_ok=True) #Crea una carpeta "PDF" Si no existe en el directorio.
        archivo = os.path.join("PDF", f"turnos_{fecha.day}-{fecha.month}-{fecha.year}.pdf") #Crea el archivo .pdf y se guarda en la carptea "PDF".
        escribir_lineas_en_pdf(columnas, filas, archivo) #Se envia a la funcion que esta en utils.py, la lista de columnas y filas, ademas de la ruta del archivo creado.

        return FileResponse(archivo, media_type="application/pdf", filename=f"turnos_{fecha.day}-{fecha.month}-{fecha.year}.pdf") #Se descarga el archivo en el buscador web
    except HTTPException:
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.


# 26.
@app.get("/reportes/turnos-cancelados-mes-actual-pdf") 
def turnos_cancelados_mes_actual_pdf(db: Session = Depends(get_db)): #Se pide una sesión de base de datos.
    try:
        hoy = date.today() #Se obtiene la fecha actual.
        inicio = hoy.replace(day=1) #primer día del mes actual.
        fin = inicio.replace(month=inicio.month + 1) if inicio.month < 12 else inicio.replace(
            year=inicio.year + 1, month=1
        ) #Primer día del mes siguiente. Si el mes es de 1 a 11 sumamos 1 al mes sino si es diciembre (12) pasamos a enero del año siguiente.

        try:
            turnos = (
                db.query(Turno)
                .filter(
                    Turno.estado == EstadoTurno.cancelado,
                    Turno.fecha >= inicio,
                    Turno.fecha < fin
                )
                .order_by(Turno.fecha.asc(), Turno.hora.asc())
                .all()
            ) #Se busca los turnos dentro del rango de dias del mes que sean cancelados y de manera ascendente en fecha y hora.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}") #Se tira una excepcion si hay un error con codigo 500.

        columnas = ["ID", "DNI", "Fecha", "Hora"] #Se crea el encabezado.
        filas = [] #Se crea el array de filas.

        for t in turnos:
            filas.append([
                t.id,
                t.persona.dni,
                t.fecha,
                t.hora.strftime("%H:%M"),
            ]) #Se muestra en un array (filas) con los turnos siguiendo el formato asignado en este bucle for.

        os.makedirs("PDF", exist_ok=True) #Crea una carpeta "PDF" Si no existe en el directorio.
        archivo = os.path.join("PDF", "turnos_cancelados_mes_actual.pdf") #Crea el archivo .pdf y se guarda en la carptea "PDF".
        escribir_lineas_en_pdf(columnas, filas, archivo) #Se envia a la funcion que esta en utils.py, la lista de columnas y filas, ademas de la ruta del archivo creado.

        return FileResponse(archivo, media_type="application/pdf", filename="turnos_cancelados_mes_actual.pdf") #Se descarga el archivo en el buscador web
    except HTTPException:
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.


# 27.
@app.get("/reportes/estado-personas-habilitadas-pdf")
def estado_personas_habilitadas_pdf(habilitada: bool, db: Session = Depends(get_db)): #Se pide de parametro "habilitada" un booleano y una sesión de base de datos.

    if habilitada is False:
        raise HTTPException(status_code=400, detail="Debe ser 'True' el valor de 'habilitada'") #Se tira una excepcion 400 ya que habilitada es "false".

    try:
        try:
            personas = (
                db.query(Persona)
                .filter(Persona.habilitado == habilitada)
                .order_by(Persona.id.asc())
                .all() 
            ) #Se busca a las personas "habilitadas" y se las ordena de manera ascendente.
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando personas: {e}") #Se tira una excepcion si hay un error con codigo 500.

        columnas = ["DNI", "Nombre", "Email", "Teléfono"] #Se crea el encabezado.
        filas = [] #Se crea el array de filas.

        for p in personas:
            filas.append([
                p.dni,
                p.nombre,
                p.email,
                p.telefono,
            ]) #Se muestra en un array (filas) con las personas siguiendo el formato asignado en este bucle for.

        os.makedirs("PDF", exist_ok=True) #Crea una carpeta "PDF" Si no existe en el directorio.
        archivo = os.path.join("PDF", "estado_personas_habilitadas.pdf") #Crea el archivo .pdf y se guarda en la carptea "PDF".
        escribir_lineas_en_pdf(columnas, filas, archivo) #Se envia a la funcion que esta en utils.py, la lista de columnas y filas, ademas de la ruta del archivo creado.

        return FileResponse(archivo, media_type="application/pdf", filename="estado_personas_habilitadas.pdf") #Se descarga el archivo en el buscador web

    except HTTPException:
        raise #Se tira alguna excepcion de HTTP si la hay.
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor") #Se tira una excepcion si hay un error con codigo 500.
