import re
import os
from io import BytesIO
from datetime import date, datetime, timedelta, time as time_cls
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Iterable, List, Optional

from BaseDatos.database import SessionLocal
from Modelos.models import Persona, Turno

from dotenv import load_dotenv
from borb.pdf import SingleColumnLayout
from borb.pdf import Document
from borb.pdf.page.page import Page
from borb.pdf.pdf import PDF
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.table.table import TableCell
from borb.pdf.canvas.layout.layout_element import Alignment


# Carga variables de entorno
load_dotenv()

# Configuración de reportes desde .env
CSV_SEPARATOR: str = os.getenv("CSV_SEPARATOR", ";")
REPORT_CSV_DIR: str = os.getenv("REPORT_CSV_DIR", "CSV")
REPORT_PDF_DIR: str = os.getenv("REPORT_PDF_DIR", "PDF")
HORA_MODELO: str = os.getenv("HORA_MODELO", "%H:%M")
SLOT_START_STR = os.getenv("SLOT_START", "09:00")
SLOT_END_STR = os.getenv("SLOT_END", "17:00")
SLOT_STEP_MIN = int(os.getenv("SLOT_STEP_MIN", "30"))
SLOT_START: time_cls = datetime.strptime(SLOT_START_STR, HORA_MODELO).time()
SLOT_END: time_cls = datetime.strptime(SLOT_END_STR, HORA_MODELO).time()
EMAIL_REGEX = os.getenv("EMAIL_REGEX")
PDF_FILAS_POR_PAGINA = int(os.getenv("PDF_FILAS_POR_PAGINA", "25"))


# --------- Sesión de base de datos --------- #

def get_db():
# Dependencia de FastAPI que abre una sesión de BDy se asegura de cerrarla al final del request.
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------- Validador de email --------- #

EMAIL_RE = re.compile(EMAIL_REGEX)


def validar_email(email: str) -> None:
# Valida el formato básico de un email. Lanza HTTPException 422 si es inválido.
    
    if not EMAIL_RE.match(email or ""):
        raise HTTPException(
            status_code=422,
            detail="Email inválido (use formato algo@dominio.com)"
        )





def _validar_slot(hora: time_cls) -> None:
# Verifica que la hora sea múltiplo de 30 minutos dentro de la franja permitida.
    
    if hora.minute not in (0, 30) or hora.second != 0 or hora.microsecond != 0:
        raise HTTPException(
            status_code=422,
            detail="La hora debe ser cada 30 minutos (HH:00 o HH:30)."
        )

    ultimo_inicio = (
        datetime.combine(date.today(), SLOT_END) - timedelta(minutes=SLOT_STEP_MIN)
    ).time()

    if not (SLOT_START <= hora <= ultimo_inicio):
        raise HTTPException(
            status_code=422,
            detail="Horario fuera de franja (09:00 a 16:30)."
        )


def parsear_hora(hhmm: str) -> time_cls:
# Parsea una hora en formato HH:MM, valida el slot y devuelve un objeto time.
    
    try:
        hora = datetime.strptime(hhmm, HORA_MODELO).time()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Hora inválida, use formato HH:MM (por ejemplo 10:30)."
        )
    _validar_slot(hora)
    return hora


def generar_slots_30min() -> List[str]:
# Genera una lista de strings con todos los horarios válidos: ['09:00', '09:30', ..., '16:30'].
    
    slots: List[str] = []
    h, m = SLOT_START.hour, SLOT_START.minute
    ultimo_inicio = (
        datetime.combine(date.today(), SLOT_END) - timedelta(minutes=SLOT_STEP_MIN)
    ).time()

    while True:
        slots.append(time_cls(h, m).strftime(HORA_MODELO))
        m += SLOT_STEP_MIN
        if m >= 60:
            m -= 60
            h += 1
        if time_cls(h, m) > ultimo_inicio:
            break
    return slots


SLOTS_FIJOS = set(generar_slots_30min())


# --------- Helpers de consulta --------- #

def persona_por_dni_o_404(db: Session, dni: int) -> Persona:
# Busca una persona por DNI. Si no existe, lanza HTTPException 404.

    persona = db.query(Persona).filter(Persona.dni == dni).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return persona


def turno_o_404(db: Session, turno_id: int) -> Turno:
# Busca un turno por ID. Si no existe, lanza HTTPException 404.

    turno = db.get(Turno, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return turno

def generar_pdf_tabla(columnas: Iterable[str], filas: Iterable[Iterable[object]], titulo: Optional[str] = None,) -> bytes:
# Genera un PDF en memoria con un título opcional y una tabla de datos. Devuelve los bytes del PDF para ser usados en un StreamingResponse.
    
    try:
        doc = Document()
        page = Page()
        doc.add_page(page)

        layout = SingleColumnLayout(page)

        cantidad = len(filas)

        # Título
        if titulo:
            layout.add(Paragraph(titulo, horizontal_alignment=Alignment.CENTERED))
            layout.add(Paragraph(" "))  # línea en blanco
        
        layout.add(Paragraph(f"Cantidad de registros: {cantidad}", horizontal_alignment=Alignment.CENTERED))

        columnas = list(columnas)
        filas = list(filas)

        tabla = FixedColumnWidthTable(
            number_of_columns=len(columnas),
            number_of_rows=len(filas) + 1,  # +1 por la fila de encabezados
        )

        # Encabezados
        for c in columnas:
            tabla.add(TableCell(Paragraph(str(c), horizontal_alignment=Alignment.CENTERED)))

        # Filas de datos
        for fila in filas:
            for valor in fila:
                tabla.add(TableCell(Paragraph(str(valor), horizontal_alignment=Alignment.CENTERED)))

        layout.add(tabla)

        buffer = BytesIO()
        PDF.dumps(buffer, doc)
        return buffer.getvalue()

    except Exception as e:
        # Esto se transforma en HTTP 500 en el endpoint
        raise RuntimeError(f"Error generando PDF con tabla: {e}")
    