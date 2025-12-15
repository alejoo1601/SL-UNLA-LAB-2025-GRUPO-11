import os
from datetime import date, timedelta
from typing import Optional, List
from sqlalchemy import func

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from Modelos.models import Persona, Turno, EstadoTurno

from Esquemas.schemas import (PersonaIn, PersonaUpdate, PersonaOut,
TurnoIn, TurnoUpdate, TurnoOut, TurnosDisponiblesOut,)

from Utilidades.utils import (get_db, validar_email, parsear_hora,SLOTS_FIJOS, generar_pdf_tabla, persona_por_dni_o_404)

from datetime import date, timedelta
from io import StringIO, BytesIO
from typing import List
import pandas as pd

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from datetime import date
from dateutil.relativedelta import relativedelta
import locale
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Configuración de reportes desde .env
MESES = os.getenv("MESES","").split(",")
HORA_MODELO: str = os.getenv("HORA_MODELO", "%H:%M")
UTF8: str = os.getenv("UTF8")

MSG_SIN_DATOS = os.getenv("MSG_SIN_DATOS")

CSV_SEPARATOR = os.getenv("CSV_SEPARATOR")
CSV_TURNOS_CANCELADOS_MES = os.getenv("CSV_TURNOS_CANCELADOS_MES")

PDF_TURNOS_CANCELADOS_MES = os.getenv("PDF_TURNOS_CANCELADOS_MES")

COLUMNAS_TURNOS_POR_FECHA = os.getenv("COL_PDF_TURNOS_POR_FECHA", "").split(",")
COLUMNAS_TURNOS_CANCELADOS_POR_MES = os.getenv("COL_PDF_TURNOS_CANCELADOS_POR_MES", "").split(",")
COLUMNAS_TURNOS_POR_PERSONA = os.getenv("COL_PDF_TURNOS_POR_PERSONA", "").split(",")
COLUMNAS_TURNOS_CANCELADOS_PERSONAS = os.getenv("COL_PDF_TURNOS_CANCELADOS_PERSONAS", "").split(",")
COLUMNAS_TURNOS_CONFIRMADOS = os.getenv("COL_PDF_TURNOS_CONFIRMADOS", "").split(",")
COLUMNAS_ESTADO_PERSONAS = os.getenv("COL_PDF_ESTADO_PERSONAS", "").split(",")
SI = os.getenv("SI")
NO = os.getenv("NO")
VARIABLE_HABILITADA = os.getenv("VARIABLE_HABILITADA")
VARIABLE_NO_HABILITADA = os.getenv("VARIABLE_NO_HABILITADA")

app = FastAPI(title="TP Grupo 11", version="1.9.2")

locale.setlocale(locale.LC_TIME, "")

# PERSONAS
# 1.
@app.post("/personas", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(datos: PersonaIn, db: Session = Depends(get_db)):
    try:
        validar_email(datos.email)

        if db.query(Persona).filter(Persona.email == datos.email).first():
            raise HTTPException(status_code=409, detail="Email ya registrado")

        if db.query(Persona).filter(Persona.dni == datos.dni).first():
            raise HTTPException(status_code=409, detail="DNI ya registrado")

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

        return PersonaOut(
            nombre=p.nombre,
            email=p.email,
            dni=p.dni,
            telefono=p.telefono,
            fecha_Nacimiento=p.fecha_Nacimiento,
            habilitado=p.habilitado,
            edad=p.edad
        )

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 2.
@app.get("/personas", response_model=List[PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    try:
        personas = db.query(Persona).order_by(Persona.id.asc()).all()

        salida = []
        for p in personas:
            edad = p.edad if hasattr(p, "edad") else None
            salida.append(
                PersonaOut(
                    nombre=p.nombre,
                    email=p.email,
                    dni=p.dni,
                    telefono=p.telefono,
                    fecha_Nacimiento=p.fecha_Nacimiento,
                    habilitado=p.habilitado,
                    edad=edad
                )
            )
        return salida

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 3.
@app.get("/personas/{dni}", response_model=PersonaOut)
def obtener_persona(dni: int, db: Session = Depends(get_db)):
    try:
        p = db.query(Persona).filter(Persona.dni == dni).first()
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        return PersonaOut(
            nombre=p.nombre,
            email=p.email,
            dni=p.dni,
            telefono=p.telefono,
            fecha_Nacimiento=p.fecha_Nacimiento,
            habilitado=p.habilitado,
            edad=p.edad
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 4.
@app.put("/personas/{dni}", response_model=PersonaOut)
def actualizar_persona(dni: int, cambios: PersonaUpdate, db: Session = Depends(get_db)):
    try:
        p = db.query(Persona).filter(Persona.dni == dni).first()
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        if cambios.nombre is not None:
            p.nombre = cambios.nombre

        if cambios.email is not None:
            validar_email(cambios.email)

            existe_otro = db.query(Persona).filter(
                Persona.email == cambios.email,
                Persona.id != p.id
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

        return PersonaOut(
            nombre=p.nombre,
            email=p.email,
            dni=p.dni,
            telefono=p.telefono,
            fecha_Nacimiento=p.fecha_Nacimiento,
            habilitado=p.habilitado,
            edad=p.edad
        )

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 5.
@app.delete("/personas/{dni}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_persona(dni: int, db: Session = Depends(get_db)):
    try:
        p = db.query(Persona).filter(Persona.dni == dni).first()
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        db.delete(p)
        db.commit()
        return None

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando persona: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# TURNOS
# 6.
@app.post("/turnos", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(datos: TurnoIn, db: Session = Depends(get_db)):
    try:
        persona = db.query(Persona).filter(Persona.dni == datos.persona_dni).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        if not persona.habilitado:
            raise HTTPException(status_code=422, detail="La persona no está habilitada")

        hace_6_meses = date.today() - timedelta(days=180)
        cancelados = db.query(Turno).filter(
            Turno.persona_id == persona.id,
            Turno.estado == EstadoTurno.cancelado,
            Turno.fecha >= hace_6_meses
        ).count()

        if cancelados >= 5:
            raise HTTPException(status_code=422, detail="La persona tiene 5 o más cancelaciones recientes")

        hora_ok = parsear_hora(datos.hora)

        colision = db.query(Turno).filter(
            Turno.fecha == datos.fecha,
            Turno.hora == hora_ok,
            Turno.estado != EstadoTurno.cancelado
        ).first()

        if colision:
            raise HTTPException(status_code=409, detail="Horario ocupado")

        turno = Turno(
            fecha=datos.fecha,
            hora=hora_ok,
            estado=datos.estado or EstadoTurno.pendiente,
            persona_id=persona.id
        )

        db.add(turno)
        db.commit()
        db.refresh(turno)

        return TurnoOut(
            id=turno.id,
            fecha=turno.fecha,
            hora=turno.hora.strftime(HORA_MODELO),
            estado=turno.estado,
            persona_dni=persona.dni
        )

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 7.
@app.get("/turnos", response_model=List[TurnoOut])
def listar_turnos(
    persona_dni: Optional[int] = None,
    estado: Optional[EstadoTurno] = None,
    fecha: Optional[date] = None,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Turno)

        if persona_dni is not None:
            persona = db.query(Persona).filter(Persona.dni == persona_dni).first()
            if not persona:
                return []
            query = query.filter(Turno.persona_id == persona.id)

        if estado is not None:
            query = query.filter(Turno.estado == estado)

        if fecha is not None:
            query = query.filter(Turno.fecha == fecha)

        turnos = query.order_by(Turno.fecha.asc(), Turno.hora.asc()).all()

        return [
            TurnoOut(
                id=t.id,
                fecha=t.fecha,
                hora=t.hora.strftime(HORA_MODELO),
                estado=t.estado,
                persona_dni=t.persona.dni
            )
            for t in turnos
        ]

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error consultando turnos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 8.
@app.get("/turnos/{turno_id}", response_model=TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        turno = db.get(Turno, turno_id)
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        return TurnoOut(
            id=turno.id,
            fecha=turno.fecha,
            hora=turno.hora.strftime(HORA_MODELO),
            estado=turno.estado,
            persona_dni=turno.persona.dni
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error consultando turno: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 9.
@app.put("/turnos/{turno_id}", response_model=TurnoOut)
def actualizar_turno(turno_id: int, cambios: TurnoUpdate, db: Session = Depends(get_db)):
    try:
        t = db.get(Turno, turno_id)
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado in (EstadoTurno.asistido, EstadoTurno.cancelado):
            raise HTTPException(status_code=422, detail="No se puede editar un turno asistido o cancelado")

        nueva_fecha = cambios.fecha or t.fecha
        nueva_hora = t.hora

        if cambios.hora is not None:
            nueva_hora = parsear_hora(cambios.hora)

        if nueva_fecha != t.fecha or nueva_hora != t.hora:
            colision = db.query(Turno).filter(
                Turno.id != t.id,
                Turno.fecha == nueva_fecha,
                Turno.hora == nueva_hora,
                Turno.estado != EstadoTurno.cancelado
            ).first()
            if colision:
                raise HTTPException(status_code=409, detail="Horario ocupado")

        if cambios.persona_dni is not None:
            p = db.query(Persona).filter(Persona.dni == cambios.persona_dni).first()
            if not p:
                raise HTTPException(status_code=404, detail="Persona destino no encontrada")
            if not p.habilitado:
                raise HTTPException(status_code=422, detail="La persona destino no está habilitada")
            t.persona_id = p.id

        t.fecha = nueva_fecha
        t.hora = nueva_hora

        if cambios.estado is not None:
            t.estado = cambios.estado

        db.commit()
        db.refresh(t)

        return TurnoOut(
            id=t.id,
            fecha=t.fecha,
            hora=t.hora.strftime(HORA_MODELO),
            estado=t.estado,
            persona_dni=t.persona.dni
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# 10.
@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        t = db.get(Turno, turno_id)
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado == EstadoTurno.asistido:
            raise HTTPException(status_code=422, detail="No se puede eliminar un turno asistido")

        db.delete(t)
        db.commit()
        return None

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")



# DISPONIBILIDAD
# 11.
@app.get("/turnos-disponibles", response_model=TurnosDisponiblesOut)
def turnos_disponibles(fecha: date, db: Session = Depends(get_db)):
    try:
        todos = set(SLOTS_FIJOS)

        bloquean = (
            db.query(Turno)
            .filter(Turno.fecha == fecha, Turno.estado != EstadoTurno.cancelado)
            .all()
        )

        ocupados = {t.hora.strftime(HORA_MODELO) for t in bloquean}
        disponibles = sorted(todos - ocupados)

        return {"fecha": fecha.isoformat(), "horarios_disponibles": disponibles}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# GESTIÓN DE ESTADO
# 12.
@app.put("/turnos/{turno_id}/cancelar", response_model=TurnoOut)
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        t = db.get(Turno, turno_id)
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado == EstadoTurno.asistido:
            raise HTTPException(
                status_code=422, detail="No se puede cancelar un turno asistido"
            )

        t.estado = EstadoTurno.cancelado
        db.commit()
        db.refresh(t)

        return TurnoOut(
            id=t.id,
            fecha=t.fecha,
            hora=t.hora.strftime(HORA_MODELO),
            estado=t.estado,
            persona_dni=t.persona.dni,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 13.
@app.put("/turnos/{turno_id}/confirmar", response_model=TurnoOut)
def confirmar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        t = db.get(Turno, turno_id)
        if not t:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        if t.estado in (EstadoTurno.asistido, EstadoTurno.cancelado):
            raise HTTPException(
                status_code=422,
                detail="No se puede confirmar un turno asistido o cancelado",
            )

        t.estado = EstadoTurno.confirmado
        db.commit()
        db.refresh(t)

        return TurnoOut(
            id=t.id,
            fecha=t.fecha,
            hora=t.hora.strftime(HORA_MODELO),
            estado=t.estado,
            persona_dni=t.persona.dni,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# REPORTES
# 14.
@app.get("/reportes/turnos-por-fecha")
def reportes_turnos_por_fecha(fecha: date, db: Session = Depends(get_db)):
    try:
        turnos = (
            db.query(Turno)
            .join(Persona)
            .filter(Turno.fecha == fecha)
            .order_by(Persona.nombre.asc(), Turno.hora.asc())
            .all()
        )

        personas = []
        persona_actual = None
        lista_actual = None
        for t in turnos:
            clave = (t.persona.dni, t.persona.nombre)
            if persona_actual != clave:
                persona_actual = clave
                lista_actual = []
                personas.append(
                    {"dni": clave[0], "nombre": clave[1], "turnos": lista_actual}
                )
            lista_actual.append(
                {"id": t.id, "hora": t.hora.strftime(HORA_MODELO), "estado": t.estado}
            )

        return {"fecha": fecha.isoformat(), "personas": personas}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 15.
@app.get("/reportes/turnos-por-persona")
def reportes_turnos_por_persona(dni: int, db: Session = Depends(get_db)):
    try:
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
            resultado.append(
                {
                    "id": t.id,
                    "fecha": t.fecha,
                    "hora": t.hora.strftime(HORA_MODELO),
                    "estado": t.estado,
                }
            )

        return {"persona": {"dni": persona.dni, "nombre": persona.nombre}, "turnos": resultado}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 16.
@app.get("/reportes/turnos-cancelados-por-mes")
def reportes_cancelados_mes(db: Session = Depends(get_db)):
    try:
        hoy = date.today()
        inicio = hoy.replace(day=1)
        fin = inicio + relativedelta(months=1)

        turnos = (
            db.query(Turno)
            .filter(
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= inicio,
                Turno.fecha < fin,
            )
            .order_by(Turno.fecha.asc(), Turno.hora.asc())
            .all()
        )

        resumen_rows = (
            db.query(Turno.fecha, func.count(Turno.id))
            .filter(
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= inicio,
                Turno.fecha < fin,
            )
            .group_by(Turno.fecha)
            .order_by(Turno.fecha.asc())
            .all()
        )
        resumen = [{"fecha": f, "cantidad": c} for (f, c) in resumen_rows]

        if len(MESES) != 12:
            raise RuntimeError("La variable de entorno MESES debe contener 12 meses")
        
        mes = MESES[hoy.month - 1]

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
                    "hora": t.hora.strftime(HORA_MODELO),
                    "estado": t.estado,
                }
                for t in turnos
            ],
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 17.
@app.get("/reportes/turnos-cancelados")
def reportes_personas_con_cancelados(min: int = 5, db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(Turno.persona_id, func.count(Turno.id))
            .filter(Turno.estado == EstadoTurno.cancelado)
            .group_by(Turno.persona_id)
            .having(func.count(Turno.id) >= min)
            .all()
        )

        salida = []
        for persona_id, cant in rows:
            p = db.query(Persona).filter(Persona.id == persona_id).first()
            t_list = (
                db.query(Turno)
                .filter(Turno.persona_id == persona_id, Turno.estado == EstadoTurno.cancelado)
                .order_by(Turno.fecha.desc(), Turno.hora.desc())
                .all()
            )

            salida.append(
                {
                    "persona": {"dni": p.dni, "nombre": p.nombre},
                    "cancelados": cant,
                    "turnos": [
                        {
                            "id": t.id,
                            "fecha": t.fecha,
                            "hora": t.hora.strftime(HORA_MODELO),
                            "estado": t.estado,
                        }
                        for t in t_list
                    ],
                }
            )

        return {"min_cancelados": min, "personas": salida}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 18.
@app.get("/reportes/turnos-confirmados")
def reportes_turnos_confirmados(
    desde: date,
    hasta: date,
    tamanio: int,
    pagina: int,
    db: Session = Depends(get_db),
):
    try:
        if desde > hasta:
            raise HTTPException(
                status_code=400,
                detail="Rango inválido: 'desde' debe ser ≤ 'hasta'",
            )

        if pagina < 1:
            pagina = 1

        q = (
            db.query(Turno)
            .filter(
                Turno.estado == EstadoTurno.confirmado,
                Turno.fecha >= desde,
                Turno.fecha <= hasta,
            )
            .order_by(Turno.fecha.asc(), Turno.hora.asc())
        )
        total = q.count()
        items = q.offset((pagina - 1) * tamanio).limit(tamanio).all()

        salida = [
            {
                "id": t.id,
                "fecha": t.fecha,
                "hora": t.hora.strftime(HORA_MODELO),
                "persona_dni": t.persona.dni,
            }
            for t in items
        ]
        total_paginas = (total + tamanio - 1) // tamanio

        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "pagina": pagina,
            "tamaño": tamanio,
            "total": total,
            "Total Paginas": total_paginas,
            "items": salida,
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 19.
@app.get("/reportes/estado-personas")
def reportes_estado_personas(habilitada: bool, db: Session = Depends(get_db)):
    try:
        personas = (
            db.query(Persona)
            .filter(Persona.habilitado == habilitada)
            .order_by(Persona.id.asc())
            .all()
        )

        salida = [
            {
                "dni": p.dni,
                "nombre": p.nombre,
                "email": p.email,
                "telefono": p.telefono,
                "habilitado": p.habilitado,
            }
            for p in personas
        ]

        return {"habilitada": habilitada, "personas": salida}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# =====================================================
# REPORTES CSV (punto G)
# =====================================================

# 20 GET /reportes/csv/turnos-por-fecha?fecha=YYYY-MM-DD
@app.get("/reportes/csv/turnos-por-fecha")
def csv_turnos_por_fecha(fecha: date, db: Session = Depends(get_db)):
    try:
        turnos = (
            db.query(Turno)
            .join(Persona)
            .filter(Turno.fecha == fecha)
            .order_by(Persona.nombre.asc(), Turno.hora.asc())
            .all()
        )

        filas = []
        for t in turnos:
            filas.append({
                "dni": t.persona.dni,
                "nombre": t.persona.nombre,
                "id_turno": t.id,
                "fecha": t.fecha.isoformat(),
                "hora": t.hora.strftime(HORA_MODELO),
                "estado": t.estado.value,
            })

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        df = pd.DataFrame(filas)

        buffer = StringIO()
        df.to_csv(buffer, sep=CSV_SEPARATOR, index=False)
        csv_bytes = buffer.getvalue().encode(UTF8)
        stream = BytesIO(csv_bytes)

        filename = f"turnos_{fecha.isoformat()}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="text/csv", headers=headers)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 21 GET /reportes/csv/turnos-cancelados-por-mes
@app.get("/reportes/csv/turnos-cancelados-por-mes")
def csv_turnos_cancelados_por_mes(db: Session = Depends(get_db)):
    try:
        hoy = date.today()
        inicio = hoy.replace(day=1)
        fin = inicio + relativedelta(months=1)

        turnos = (
            db.query(Turno)
            .join(Persona)
            .filter(
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= inicio,
                Turno.fecha < fin,
            )
            .order_by(Turno.fecha.asc(), Turno.hora.asc())
            .all()
        )

        filas = []
        for t in turnos:
            filas.append({
                "id": t.id,
                "dni": t.persona.dni,
                "nombre": t.persona.nombre,
                "fecha": t.fecha.isoformat(),
                "hora": t.hora.strftime(HORA_MODELO),
            })

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        df = pd.DataFrame(filas)

        buffer = StringIO()
        df.to_csv(buffer, sep=CSV_SEPARATOR, index=False)
        csv_bytes = buffer.getvalue().encode(UTF8)
        stream = BytesIO(csv_bytes)

        filename = CSV_TURNOS_CANCELADOS_MES
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="text/csv", headers=headers)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 22 GET /reportes/csv/turnos-por-persona?dni=12345678
@app.get("/reportes/csv/turnos-por-persona")
def csv_turnos_por_persona(dni: int, db: Session = Depends(get_db)):
    try:
        persona = persona_por_dni_o_404(db, dni)

        turnos = (
            db.query(Turno)
            .filter(Turno.persona_id == persona.id)
            .order_by(Turno.fecha.desc(), Turno.hora.desc())
            .all()
        )

        filas = []
        for t in turnos:
            filas.append({
                "id": t.id,
                "fecha": t.fecha.isoformat(),
                "hora": t.hora.strftime(HORA_MODELO),
                "estado": t.estado.value,
            })

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        df = pd.DataFrame(filas)

        buffer = StringIO()
        df.to_csv(buffer, sep=CSV_SEPARATOR, index=False)
        csv_bytes = buffer.getvalue().encode(UTF8)
        stream = BytesIO(csv_bytes)

        filename = f"turnos_{persona.nombre}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="text/csv", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 23 GET /reportes/csv/turnos-cancelados?min=5
@app.get("/reportes/csv/turnos-cancelados")
def csv_turnos_cancelados_por_persona(min: int = 5, db: Session = Depends(get_db)):
    try:
        hoy = date.today()
        hace_6_meses = hoy - timedelta(days=180)  # aproximación 6 meses

        resultados = (
            db.query(
                Persona.dni,
                Persona.nombre,
                func.count(Turno.id).label("cantidad_cancelados"),
            )
            .join(Turno)
            .filter(
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= hace_6_meses,
                Turno.fecha <= hoy,
            )
            .group_by(Persona.id)
            .having(func.count(Turno.id) >= min)
            .order_by(func.count(Turno.id).desc())
            .all()
        )

        filas = []
        for dni_persona, nombre, cant in resultados:
            filas.append({
                "dni": dni_persona,
                "nombre": nombre,
                "cancelados_ultimos_6_meses": cant,
            })

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        df = pd.DataFrame(filas)

        buffer = StringIO()
        df.to_csv(buffer, sep=CSV_SEPARATOR, index=False)
        csv_bytes = buffer.getvalue().encode(UTF8)
        stream = BytesIO(csv_bytes)

        filename = f"personas_con_{min}_o_mas_cancelados.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="text/csv", headers=headers)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 24 GET /reportes/csv/turnos-confirmados?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
@app.get("/reportes/csv/turnos-confirmados")
def csv_turnos_confirmados(
    desde: date,
    hasta: date,
    db: Session = Depends(get_db),
):
    try:
        turnos = (
            db.query(Turno)
            .join(Persona)
            .filter(
                Turno.estado == EstadoTurno.confirmado,
                Turno.fecha >= desde,
                Turno.fecha <= hasta,
            )
            .order_by(Turno.fecha.asc(), Turno.hora.asc())
            .all()
        )

        filas = []
        for t in turnos:
            filas.append({
                "dni": t.persona.dni,
                "nombre": t.persona.nombre,
                "id_turno": t.id,
                "fecha": t.fecha.isoformat(),
                "hora": t.hora.strftime(HORA_MODELO),
            })

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        df = pd.DataFrame(filas)

        buffer = StringIO()
        df.to_csv(buffer, sep=CSV_SEPARATOR, index=False)
        csv_bytes = buffer.getvalue().encode(UTF8)
        stream = BytesIO(csv_bytes)

        filename = f"turnos_confirmados_{desde}_a_{hasta}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="text/csv", headers=headers)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 25 GET /reportes/csv/estado-personas?habilitada=true/false
@app.get("/reportes/csv/estado-personas")
def csv_estado_personas(habilitada: bool, db: Session = Depends(get_db)):
    try:
        personas = (
            db.query(Persona)
            .filter(Persona.habilitado == habilitada)
            .order_by(Persona.id.asc())
            .all()
        )

        filas = []
        for p in personas:
            filas.append({
                "dni": p.dni,
                "nombre": p.nombre,
                "email": p.email,
                "telefono": p.telefono,
                "habilitado": p.habilitado,
            })

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        df = pd.DataFrame(filas)

        buffer = StringIO()
        df.to_csv(buffer, sep=CSV_SEPARATOR, index=False)
        csv_bytes = buffer.getvalue().encode(UTF8)
        stream = BytesIO(csv_bytes)

        estado = "habilitadas" if habilitada else "no_habilitadas"
        filename = f"personas_{estado}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="text/csv", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
# =====================================================
# REPORTES PDF (punto F)
# =====================================================

# 26
@app.get("/reportes/pdf/turnos-por-fecha")
def pdf_turnos_por_fecha(fecha: date, db: Session = Depends(get_db)):
    try:
        turnos = (
            db.query(Turno)
            .join(Persona)
            .filter(Turno.fecha == fecha)
            .order_by(Persona.nombre.asc(), Turno.hora.asc())
            .all()
        )

        columnas = COLUMNAS_TURNOS_POR_FECHA
        filas = []
        for t in turnos:
            filas.append([
                t.persona.dni,
                t.persona.nombre,
                t.id,
                t.fecha,
                t.hora.strftime(HORA_MODELO),
                t.estado.value,
            ])

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        titulo = f"Turnos del día {fecha.isoformat()}"
        pdf_bytes = generar_pdf_tabla(columnas, filas, titulo=titulo)
        stream = BytesIO(pdf_bytes)

        filename = f"turnos_{fecha.isoformat()}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 27
@app.get("/reportes/pdf/turnos-cancelados-por-mes")
def pdf_turnos_cancelados_por_mes(db: Session = Depends(get_db)):
    try:
        hoy = date.today()
        inicio = hoy.replace(day=1)
        fin = inicio + relativedelta(months=1)

        turnos = (
            db.query(Turno)
            .join(Persona)
            .filter(
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= inicio,
                Turno.fecha < fin,
            )
            .order_by(Turno.fecha.asc(), Turno.hora.asc())
            .all()
        )

        columnas = COLUMNAS_TURNOS_CANCELADOS_POR_MES
        filas = []
        for t in turnos:
            filas.append([
                t.id,
                t.persona.dni,
                t.persona.nombre,
                t.fecha,
                t.hora.strftime(HORA_MODELO),
            ])

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        titulo = f"Turnos cancelados del mes {inicio.month}/{inicio.year}"
        pdf_bytes = generar_pdf_tabla(columnas, filas, titulo=titulo)
        stream = BytesIO(pdf_bytes)

        filename = PDF_TURNOS_CANCELADOS_MES
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 28
@app.get("/reportes/pdf/turnos-por-persona")
def pdf_turnos_por_persona(dni: int, db: Session = Depends(get_db)):
    try:
        persona = persona_por_dni_o_404(db, dni)

        turnos = (
            db.query(Turno)
            .filter(Turno.persona_id == persona.id)
            .order_by(Turno.fecha.desc(), Turno.hora.desc())
            .all()
        )

        columnas = COLUMNAS_TURNOS_POR_PERSONA
        filas = []
        for t in turnos:
            filas.append([
                t.id,
                t.fecha,
                t.hora.strftime(HORA_MODELO),
                t.estado.value,
            ])

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        titulo = f"Turnos de {persona.nombre} (DNI: {persona.dni})"
        pdf_bytes = generar_pdf_tabla(columnas, filas, titulo=titulo)
        stream = BytesIO(pdf_bytes)

        filename = f"turnos_{persona.nombre}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 29
@app.get("/reportes/pdf/turnos-cancelados")
def pdf_turnos_cancelados_por_persona(min: int = 5, db: Session = Depends(get_db)):
    try:
        hoy = date.today()
        hace_6_meses = hoy - timedelta(days=180)

        resultados = (
            db.query(
                Persona.dni,
                Persona.nombre,
                func.count(Turno.id).label("cantidad_cancelados"),
            )
            .join(Turno)
            .filter(
                Turno.estado == EstadoTurno.cancelado,
                Turno.fecha >= hace_6_meses,
                Turno.fecha <= hoy,
            )
            .group_by(Persona.id)
            .having(func.count(Turno.id) >= min)
            .order_by(func.count(Turno.id).desc())
            .all()
        )

        columnas = COLUMNAS_TURNOS_CANCELADOS_PERSONAS
        filas = []
        for dni_persona, nombre, cant in resultados:
            filas.append([dni_persona, nombre, cant])

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        titulo = f"Personas con {min} o más turnos cancelados en los últimos 6 meses"
        pdf_bytes = generar_pdf_tabla(columnas, filas, titulo=titulo)
        stream = BytesIO(pdf_bytes)

        filename = f"personas_con_{min}_o_mas_cancelados.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# 30
@app.get("/reportes/pdf/turnos-confirmados")
def pdf_turnos_confirmados(
    desde: date,
    hasta: date,
    tamanio: int,
    pagina: int,
    db: Session = Depends(get_db),
):
    try:
        if pagina < 1:
            pagina = 1
        if tamanio < 1:
            tamanio = 50

        q = (
            db.query(Turno)
            .join(Persona)
            .filter(
                Turno.estado == EstadoTurno.confirmado,
                Turno.fecha >= desde,
                Turno.fecha <= hasta,
            )
            .order_by(Turno.fecha.asc(), Turno.hora.asc())
        )

        total = q.count()
        turnos = q.offset((pagina - 1) * tamanio).limit(tamanio).all()

        columnas = COLUMNAS_TURNOS_CONFIRMADOS
        filas = []
        for t in turnos:
            filas.append([
                t.persona.dni,
                t.persona.nombre,
                t.id,
                t.fecha,
                t.hora.strftime(HORA_MODELO),
            ])

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        titulo = f"Turnos confirmados entre {desde} y {hasta} (página {pagina}) - Total: {total}"
        pdf_bytes = generar_pdf_tabla(columnas, filas, titulo=titulo)
        stream = BytesIO(pdf_bytes)

        filename = f"turnos_confirmados_{desde}_a_{hasta}_p{pagina}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")



# 31
@app.get("/reportes/pdf/estado-personas")
def pdf_estado_personas(habilitada: bool, db: Session = Depends(get_db)):
    try:
        personas = (
            db.query(Persona)
            .filter(Persona.habilitado == habilitada)
            .order_by(Persona.id.asc())
            .all()
        )

        if len(COLUMNAS_ESTADO_PERSONAS) != 5:
            raise RuntimeError("La variable COLUMNAS_ESTADO_PERSONAS debe tener 5 valores separados por coma")

        columnas = columnas = COLUMNAS_ESTADO_PERSONAS
        filas = []
        for p in personas:
            filas.append([
                p.dni,
                p.nombre,
                p.email,
                p.telefono,
                SI if p.habilitado else NO,
            ])

        if not filas:
            raise HTTPException(status_code=404, detail=MSG_SIN_DATOS)

        estado = VARIABLE_HABILITADA if habilitada else VARIABLE_NO_HABILITADA
        titulo = f"Personas {estado}"
        pdf_bytes = generar_pdf_tabla(columnas, filas, titulo=titulo)
        stream = BytesIO(pdf_bytes)

        filename = f"personas_{estado.replace(' ', '_')}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

