# Sistema Gestor de Consultas y Expedientes de Pacientes
Proyecto Integrador II · UNAN-León · Grupo GP4

Aplicación de escritorio en **Python + PySide6** con **SQLAlchemy** (SQLite por defecto, MySQL opcional),
construida sobre la arquitectura en capas del informe final.

## Cómo ejecutarlo
```
pip install -r requirements.txt
python main.py
```
La primera vez se crea `sistema_consultas.db` con datos de demostración (12 pacientes, 8 expedientes,
18 consultas, 4 médicos). Para empezar de cero, borre ese archivo.

| Perfil | Usuario | Contraseña |
|---|---|---|
| Administrador | admin | admin123 |
| Médico | doctor | doctor123 |
| Enfermería | enfermera | enfermera123 |

## Estructura (capas del documento)
| Archivo | Capa |
|---|---|
| `models.py` | Dominio + mapeo ORM de las 11 tablas (IMC y reglas de la entidad) |
| `controller.py` | Lógica de negocio, validaciones, permisos (RBAC) y bitácora |
| `reportes_pdf.py` | Reportes PDF (RF-11) |
| `database.py`, `seed.py`, `permisos.py`, `security.py` | Persistencia, datos iniciales, matriz de permisos, hash de contraseñas |
| `main.py` + `vistas/` | Presentación (PySide6). La interfaz solo llama al controlador |

## Roles y permisos
La Tabla 10 del documento se siembra como matriz inicial. El **administrador** puede cambiarla desde
**Usuarios y permisos → Permisos por rol** (interruptores por funcionalidad para Médico y Enfermería) y crear
cuentas. Los cambios se guardan en `roles_permisos` y se aplican en el siguiente inicio de sesión del usuario.
El menú y los botones de cada pantalla se adaptan a los permisos.

## Historial de consultas
Al seleccionar un expediente (módulo Expedientes o Consultas) las consultas se listan **de la más reciente a la
más antigua** (`fecha DESC`, luego `id_consulta DESC`). Esto está definido en la relación `Expediente.consultas`
y en `ConsultaController.historial()`, y también se respeta en el PDF del expediente.

## MySQL (opcional)
```
pip install pymysql
set DATABASE_URL=mysql+pymysql://usuario:clave@localhost/sistema_consultas_medicas?charset=utf8mb4
python main.py
```
