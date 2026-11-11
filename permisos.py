# Archivo: permisos.py
# Catálogo de permisos y matriz por defecto (Tabla 10 del documento).
# El administrador puede cambiar después los permisos de doctor y enfermera
# desde el sistema (Usuarios y permisos > Permisos por rol); lo que se guarda
# en la tabla roles_permisos prevalece sobre esta matriz inicial.

# (clave, descripción, módulo)
PERMISOS = [
    ("panel.ver",            "Ver el panel general y las estadísticas",           "Inicio"),
    ("pacientes.ver",        "Consultar pacientes",                               "Pacientes"),
    ("pacientes.editar",     "Registrar, modificar y dar de baja pacientes",      "Pacientes"),
    ("expedientes.ver",      "Consultar expedientes clínicos",                    "Expedientes"),
    ("expedientes.editar",   "Abrir y modificar expedientes clínicos",            "Expedientes"),
    ("consultas.ver",        "Consultar el historial de consultas",               "Consultas"),
    ("consultas.registrar",  "Registrar, modificar y eliminar consultas médicas", "Consultas"),
    ("citas.ver",            "Consultar la agenda de citas",                      "Citas"),
    ("citas.editar",         "Programar y cancelar citas",                        "Citas"),
    ("medicos.gestionar",    "Gestionar médicos y especialidades",                "Médicos"),
    ("reportes.generar",     "Generar reportes en PDF",                           "Reportes"),
    ("usuarios.gestionar",   "Administrar usuarios, roles y permisos",            "Administración"),
    ("bitacora.ver",         "Consultar la bitácora de auditoría",                "Administración"),
]

ROLES = {
    "admin": "Responsable de la configuración y supervisión del sistema.",
    "doctor": "Médico que atiende a los pacientes.",
    "enfermera": "Personal de apoyo que recibe y registra pacientes.",
}

ETIQUETA_ROL = {"admin": "Administrador", "doctor": "Médico", "enfermera": "Enfermería"}

_TODOS = [p[0] for p in PERMISOS]

MATRIZ_POR_DEFECTO = {
    # Administrador: todo, salvo registrar consultas (en la matriz solo "Consulta")
    "admin": [c for c in _TODOS if c != "consultas.registrar"],
    "doctor": ["panel.ver", "pacientes.ver", "expedientes.ver", "expedientes.editar",
               "consultas.ver", "consultas.registrar", "citas.ver", "citas.editar",
               "reportes.generar"],
    "enfermera": ["panel.ver", "pacientes.ver", "pacientes.editar", "expedientes.ver",
                  "consultas.ver", "citas.ver", "citas.editar"],
}
