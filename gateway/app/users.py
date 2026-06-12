"""Usuarios de prueba del ecosistema.

Cada usuario representa un actor del negocio y su portal correspondiente.
En un entorno real esto vendria de un proveedor de identidad.
"""

USERS = {
    "secretaria": {
        "password": "campus123",
        "name": "Secretaria Academica",
        "role": "academico",
    },
    "finanzas": {
        "password": "campus123",
        "name": "Area Financiera",
        "role": "pagos",
    },
    "docente": {
        "password": "campus123",
        "name": "Docente / Bienestar",
        "role": "docente",
    },
    "director": {
        "password": "campus123",
        "name": "Direccion",
        "role": "director",
    },
}
