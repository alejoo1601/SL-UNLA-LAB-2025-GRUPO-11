# SL-UNLA-LAB-2025-GRUPO-11

Integrantes Grupo 11:

* Ivan Kersevan
* Matias Torres de Lima
* Alejo Tomas Machado Prieto
* Tomas Ezequiel Laruina Inchausti 

Link video YouTube:
HITO 1:
https://youtu.be/CxaVbo8jo28

HITO 2:
https://youtu.be/NWY2hYGvF7o

Link colleccion Postman:
https://ivankersevan13-8355299.postman.co/workspace/TP-Seminario-Python-Grupo-11's-~6da58f10-1211-4bdb-82bb-be7bc22ba18d/collection/48622493-a74a7414-05ad-4dea-bb09-97fbbc4bdbd9?action=share&source=copy-link&creator=48622493

Link Repositorio Github:
https://github.com/alejoo1601/SL-UNLA-LAB-2025-GRUPO-11


Instrucciones para ejecutar el proyecto:
* Clonar el repositorio:
git clone https://github.com/alejoo1601/SL-UNLA-LAB-2025-GRUPO-11.git

* Ingresar a la carpeta del proyecto:
cd SL-UNLA-LAB-2025-GRUPO-11

* Crear el entorno virtual:
python -m venv venv

* Activar el entorno virtual:
En Windows: venv\Scripts\activate
En Linux/Mac: source venv/bin/activate

* Instalar las dependencias:
pip install -r requirements.txt

* Ejecutar la aplicación:
uvicorn app:app --reload

* Abrir en el navegador: http://127.0.0.1:8000/docs

Endpoints:

* Personas:
1. POST /personas — Crear persona (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    200/201: persona creada (edad ya calculada).
    409: DNI o email ya registrados.
    422: email/formato inválido.

2. GET /personas — Listar personas (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    200: array de personas.

3. GET /personas/{dni} — Obtener persona por DNI (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    200: persona (incluye edad).
    404: no existe.

4. PUT /personas/{dni} — Actualizar persona (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    200: persona actualizada (incluye edad).
    404: no existe.
    409: email en uso por otra persona.

5. DELETE /personas/{dni} — Eliminar persona (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    204: eliminado.
    404: no existe.

* Turnos:
6. POST /turnos — Crear turno (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Reglas:
     * Bloquea si la persona tiene ≥5 cancelados en los últimos 6 meses.
     * Impide doble reserva del mismo fecha y hora.
    201: turno creado.
    404: persona inexistente.
    422: persona no habilitada o regla de 5 cancelados.
    409: fecha y hora ocupado.

7. GET /turnos — Listar turnos (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    200: array de turnos.

8. GET /turnos/{id} — Obtener turno por ID (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    200: turno.
    404: no existe.

9. PUT /turnos/{id}/confirmar — Actualizar turno (confirmado) (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Reglas:
     * Si cambian fecha/hora, valida colisión (409).
     * Si cambian persona_dni, valida persona habilitada (422).
    200: turno actualizado a confirmado.
    404: no existe.

10. DELETE /turnos/{id}/cancelar  — Eliminar turno (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    204: eliminado.
    404: no existe.

* Disponibilidad:
11. GET /turnos-disponibles — Horarios libres por fecha (Ivan Kersevan)
    Lógica: devuelve slots 09:00–17:00 cada 30 minutos excluyendo horarios con turnos pendiente|confirmado|asistido. Los cancelado no bloquean (liberan el horario).
    200/201: OK / Creado
    204: Sin contenido (eliminacion)
    404: No encontrado
    409: Conflicto (unicidad de email/DNI o colisión fecha y hora)
    422: Regla de negocio / Validación (persona no habilitada, 5 cancelados/6 meses, formato hora/email)

* Gestión de estado de turno:
12. PUT /turnos/{id}/cancelar — Cancelar turno (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Reglas:
    * No se puede cancelar un turno asistido (422).
    * Si el turno ya está cancelado, el endpoint es idempotente: devuelve el turno tal cual.
    Respuestas:
    200: turno (id, fecha, hora, estado, persona_dni).
    404: turno inexistente.
    422: “No se puede cancelar un turno asistido”. 

13. PUT /turnos/{id}/confirmar — Confirmar turno (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Reglas:
    * No se puede confirmar si el turno está asistido o cancelado (422).
    * Si ya estaba confirmado, es idempotente: devuelve el turno tal cual.
    Respuestas:
    200: turno (id, fecha, hora, estado, persona_dni).
    404: turno inexistente.
    422: “No se puede confirmar un turno asistido o cancelado”. 

* Reportes:
14. GET /reportes/turnos-por-fecha — Turnos de una fecha (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    Query: fecha (YYYY-MM-DD, requerido)
    200: OK
    404: si no hay turnos devuelve lista vacía

15. GET /reportes/turnos-por-persona — Turnos por DNI (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    Query: dni (int, requerido)
    200: OK
    404: no existe el dni.
    
16. GET /reportes/turnos-cancelados-por-mes — Cancelados en el mes actual (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    200: OK

17. GET /reportes/turnos-cancelados — Personas con N o más cancelados (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    200: OK

18. GET /reportes/turnos-confirmados — Confirmados por rango (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Query: desde (YYYY-MM-DD, req.), hasta (YYYY-MM-DD, req.), page (int, default 1; tamaño de página=5)
    200: OK
    404: Rango de fechas inválido.

19. GET /reportes/estado-personas — Personas habilitadas / inhabilitadas (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    Query: habilitada (bool, requerido: true o false)
    200: OK

* Reportes CSV:
20. GET /reportes/turnos-por-persona-csv — Exporta los turnos de una persona en formato CSV (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    Query: dni (int, requerido)
    200: archivo CSV descargable.
    404: persona no encontrada.
    500: error generando archivo.

21. GET /reportes/turnos-por-fecha-csv — Exporta los turnos de una fecha en formato CSV (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    Query: fecha (YYYY-MM-DD, requerido)
    200: archivo CSV descargable.
    500: error generando archivo.

22. GET /reportes/turnos-cancelados-mes-actual-csv — Exporta los turnos cancelados del mes actual (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    200: archivo CSV descargable.
    500: error generando archivo.

23. GET /reportes/estado-personas-habilitadas-csv — Exporta todas las personas según estado de habilitación (Matias Torres de Lima y Alejo Tomas Machado Prieto)
    Query: habilitada (bool, requerido)
    200: archivo CSV descargable.
    400: error de booleano ingresado.
    500: error generando archivo.

* Reportes PDF:
24. GET /reportes/turnos-por-persona-pdf — PDF con los turnos de una persona (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Query: dni (int, requerido)
    Incluye título con nombre y DNI y una tabla con: ID, Fecha, Hora, Estado.
    200: PDF descargable.
    404: persona no encontrada.
    500: error generando PDF.

25. GET /reportes/turnos-por-fecha-pdf — PDF con los turnos de una fecha (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Query: fecha (YYYY-MM-DD, requerido)
    Tabla: DNI, Nombre, ID Turno, Hora, Estado.
    200: PDF descargable.
    500: error generando PDF.

26. GET /reportes/turnos-cancelados-mes-actual-pdf — PDF con turnos cancelados del mes actual (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Tabla: ID, DNI, Fecha, Hora.
    200: PDF descargable.
    500: error generando PDF.

27. GET /reportes/estado-personas-habilitadas-pdf — PDF con personas habilitadas (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Query: habilitada (bool, requerido)
    Tabla: DNI, Nombre, Email, Teléfono.
    200: PDF descargable.
    400: error de booleano ingresado.
    500: error generando PDF.

Notas sobre exportación CSV/PDF:
* Los CSV se generan con separador `;` y sin índice.
* Los PDF se generan con la librería borb (v2.1.5).
* Las carpetas se crean automáticamente si no existen.
* Los archivos se guardan en las carpetas "PDF" Y "CSV" respectivamente antes de ser devueltos.
* Se aplican try/except en cada endpoint para capturar errores de formato o generación.
