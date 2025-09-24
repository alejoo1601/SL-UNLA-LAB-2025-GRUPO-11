# SL-UNLA-LAB-2025-GRUPO-11

Integrantes Grupo 11:

* Ivan Kersevan
* Matias Torres de Lima
* Alejo Tomas Machado Prieto
* Tomas Ezequiel Laruina Inchausti 

Link video YouTube:
https://youtu.be/CxaVbo8jo28

Link colleccion Postman:
https://ivankersevan13-8355299.postman.co/workspace/TP-Seminario-Python-Grupo-11's-~6da58f10-1211-4bdb-82bb-be7bc22ba18d/collection/48622493-60304d01-083a-4e7b-b5ca-cfa1125d8a0f?action=share&source=copy-link&creator=48622493

Link Repositorio Github:
https://github.com/alejoo1601/SL-UNLA-LAB-2025-GRUPO-11

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

9. PUT /turnos/{id} — Actualizar turno (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
    Reglas:
     * Si cambian fecha/hora, valida colisión (409).
     * Si cambian persona_dni, valida persona habilitada (422).
    200: turno actualizado.
    404: no existe.

10. DELETE /turnos/{id} — Eliminar turno (Ivan Kersevan y Tomas Ezequiel Laruina Inchausti)
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

