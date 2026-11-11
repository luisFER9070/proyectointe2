# Archivo: seed.py
# Siembra los datos iniciales la primera vez que se ejecuta el sistema:
# roles, permisos (matriz de la Tabla 10), especialidades, médicos, usuarios de
# demostración y los 12 pacientes / 8 expedientes / 18 consultas del informe.
from datetime import date, datetime, timedelta

from sqlalchemy import select

from models import (Cita, Consulta, Especialidad, Expediente, Medico, Paciente,
                    Permiso, Rol, Usuario)
from permisos import MATRIZ_POR_DEFECTO, PERMISOS, ROLES
from security import hash_password

CREDENCIALES_DEMO = {
    "admin": ("admin", "admin123"),
    "doctor": ("doctor", "doctor123"),
    "enfermera": ("enfermera", "enfermera123"),
}


def sembrar_si_vacia(db) -> bool:
    s = db.session
    if s.scalar(select(Rol).limit(1)) is not None:
        return False

    # --- Seguridad: roles, permisos y matriz inicial ---
    permisos = {c: Permiso(clave=c, descripcion=d) for c, d, _m in PERMISOS}
    roles = {n: Rol(nombre=n, descripcion=d) for n, d in ROLES.items()}
    for nombre, claves in MATRIZ_POR_DEFECTO.items():
        roles[nombre].permisos = [permisos[c] for c in claves]
    s.add_all(list(permisos.values()) + list(roles.values()))

    # --- Personal médico ---
    esp = {n: Especialidad(nombre=n, descripcion=d) for n, d in [
        ("Medicina General", "Atención primaria y control integral del paciente."),
        ("Medicina Interna", "Diagnóstico y tratamiento de enfermedades del adulto."),
        ("Ginecología", "Salud de la mujer y control prenatal."),
        ("Cardiología", "Enfermedades del corazón y el sistema circulatorio."),
    ]}
    s.add_all(esp.values())
    medicos = [
        Medico(codigo="MED-001", nombre_completo="Dra. Elena Cruz Palacios",
               especialidad=esp["Medicina General"], telefono="8855-1201", activo=1),
        Medico(codigo="MED-002", nombre_completo="Dr. Marvin Sandoval Ruiz",
               especialidad=esp["Medicina Interna"], telefono="8855-1202", activo=1),
        Medico(codigo="MED-003", nombre_completo="Dra. Lourdes Baltodano Mena",
               especialidad=esp["Ginecología"], telefono="8855-1203", activo=1),
        Medico(codigo="MED-004", nombre_completo="Dr. Néstor Obando Tellez",
               especialidad=esp["Cardiología"], telefono="8855-1204", activo=1),
    ]
    s.add_all(medicos)

    # --- Usuarios de demostración (contraseña guardada como hash) ---
    s.add_all([
        Usuario(username="admin", nombre_completo="Administrador del Sistema",
                password_hash=hash_password("admin123"), rol=roles["admin"]),
        Usuario(username="doctor", nombre_completo="Dra. Elena Cruz Palacios",
                password_hash=hash_password("doctor123"), rol=roles["doctor"], medico=medicos[0]),
        Usuario(username="enfermera", nombre_completo="Enf. Rosa Valle Ortiz",
                password_hash=hash_password("enfermera123"), rol=roles["enfermera"]),
    ])

    # --- Pacientes de demostración (12, como en el informe) ---
    datos = [
        ("001-010190-0001A", "Maria Fernanda Lopez Gutierrez", 34, "Femenino", "8801-1001", 62.0, 1.62),
        ("001-020285-0002B", "Carlos Alberto Rivas Mendoza", 40, "Masculino", "8801-1002", 80.5, 1.75),
        ("001-030792-0003C", "Ana Lucia Martinez Sequeira", 28, "Femenino", "8801-1003", 55.3, 1.58),
        ("001-041188-0004D", "Jose Ramon Hernandez Baez", 55, "Masculino", "8801-1004", 90.2, 1.70),
        ("001-051095-0005E", "Karla Vanessa Jarquin Ortega", 25, "Femenino", "8801-1005", 58.0, 1.60),
        ("001-060380-0006F", "Luis Fernando Aguilar Reyes", 61, "Masculino", "8801-1006", 78.4, 1.68),
        ("001-070697-0007G", "Silvia Patricia Cano Morales", 22, "Femenino", "8801-1007", 50.1, 1.55),
        ("001-080489-0008H", "Roberto Antonio Zeledon Tellez", 47, "Masculino", "8801-1008", 95.0, 1.80),
        ("001-090991-0009I", "Gabriela del Carmen Rocha Vado", 31, "Femenino", "8801-1009", 65.7, 1.64),
        ("001-100283-0010J", "Manuel Esteban Cruz Delgado", 66, "Masculino", "8801-1010", 72.3, 1.66),
        ("001-110584-0011K", "Paola Andrea Chavarria Solis", 19, "Femenino", "8801-1011", 48.9, 1.59),
        ("001-120686-0012L", "Diego Alejandro Narvaez Roque", 38, "Masculino", "8801-1012", 88.0, 1.77),
    ]
    pacientes = [Paciente(cedula=c, nombre_completo=n, edad=e, sexo=sx, telefono=t,
                          peso_kg=p, altura_m=a) for c, n, e, sx, t, p, a in datos]
    s.add_all(pacientes)

    # --- Expedientes (8 de los 12 pacientes; 4 quedan sin expediente) ---
    fichas = [
        ("O+", "Penicilina", "Gastritis crónica leve"),
        ("A+", "Ninguna conocida", "Padre con hipertensión arterial"),
        ("B+", "Ninguna conocida", "Primer embarazo en curso"),
        ("O-", "Sulfas", "Diabetes mellitus en la familia"),
        ("AB+", "Ninguna conocida", "Infecciones urinarias recurrentes"),
        ("A-", "Ibuprofeno", "Ex fumador, hipertensión controlada"),
        ("O+", "Ninguna conocida", "Sin antecedentes relevantes"),
        ("B-", "Polvo y ácaros", "Hernia discal operada en 2019"),
    ]
    expedientes = []
    for i, (sangre, alergia, antec) in enumerate(fichas):
        expedientes.append(Expediente(
            numero=f"EXP-{i + 1:04d}", paciente=pacientes[i], tipo_sangre=sangre,
            alergias=alergia, antecedentes=antec,
            fecha_apertura=date(2025, 6, 1) + timedelta(days=i * 17)))
    s.add_all(expedientes)

    # --- Consultas (18): (expediente, fecha, médico, motivo, diagnóstico, tratamiento, obs.) ---
    c = [
        (0, date(2026, 10, 14), 2, "Control ginecológico anual", "Control ginecológico normal",
         "Continuar control anual", "Sin hallazgos de importancia."),
        (0, date(2026, 8, 3), 0, "Cefalea persistente", "Cefalea tensional",
         "Paracetamol 500 mg cada 8 horas por 3 días", "Reducir estrés y tiempo de pantalla."),
        (0, date(2026, 4, 22), 0, "Dolor abdominal", "Gastritis aguda",
         "Omeprazol 20 mg en ayunas por 14 días", "Dieta blanda; evitar irritantes."),
        (0, date(2025, 12, 10), 0, "Tos y malestar general", "Gripe común",
         "Reposo, líquidos y paracetamol", "Evolución favorable."),
        (1, date(2026, 10, 20), 3, "Dolor de pecho leve", "Hipertensión arterial",
         "Losartán 50 mg una vez al día", "Control de presión en 15 días."),
        (1, date(2026, 9, 30), 1, "Chequeo general", "Hipertensión arterial",
         "Dieta baja en sodio y caminata diaria", "Presión 150/95 mmHg."),
        (1, date(2026, 6, 18), 0, "Fiebre y dolor de garganta", "Gripe común",
         "Paracetamol y abundantes líquidos", "Sin signos de alarma."),
        (2, date(2026, 10, 9), 2, "Control prenatal", "Embarazo normal",
         "Ácido fólico y hierro diarios", "Ecografía programada."),
        (2, date(2026, 9, 9), 2, "Control prenatal", "Embarazo normal",
         "Ácido fólico y hierro diarios", "Peso y presión adecuados."),
        (2, date(2026, 7, 15), 0, "Náuseas matutinas", "Embarazo normal",
         "Fraccionar comidas", "Se refiere a control prenatal."),
        (3, date(2026, 10, 22), 1, "Control de glucosa", "Diabetes mellitus tipo 2",
         "Metformina 850 mg cada 12 horas", "Glucemia en ayunas 142 mg/dl."),
        (3, date(2026, 8, 19), 1, "Sed excesiva y fatiga", "Diabetes mellitus tipo 2",
         "Inicio de metformina y dieta", "Se solicitan exámenes de laboratorio."),
        (3, date(2026, 5, 11), 3, "Palpitaciones", "Hipertensión arterial",
         "Control de presión y reducción de sal", "Electrocardiograma sin alteraciones."),
        (4, date(2026, 10, 2), 0, "Ardor al orinar", "Infección urinaria",
         "Nitrofurantoína 100 mg cada 12 horas por 5 días", "Aumentar consumo de agua."),
        (4, date(2026, 3, 27), 0, "Tos y congestión nasal", "Gripe común",
         "Antihistamínico y reposo", "Sin fiebre."),
        (5, date(2026, 10, 26), 3, "Falta de aire al esfuerzo", "Insuficiencia cardíaca leve",
         "Furosemida 20 mg por la mañana", "Referir a ecocardiograma."),
        (6, date(2026, 9, 14), 0, "Dolor de garganta", "Faringitis aguda",
         "Amoxicilina 500 mg cada 8 horas por 7 días", "Control si persiste la fiebre."),
        (7, date(2026, 7, 29), 1, "Dolor lumbar", "Lumbalgia mecánica",
         "Diclofenac y ejercicios de estiramiento", "Evitar cargar peso."),
    ]
    c.sort(key=lambda x: x[1])                      # códigos correlativos por fecha
    for n, (e, fecha, m, motivo, diag, trat, obs) in enumerate(c, start=1):
        s.add(Consulta(codigo=f"CON-{n:04d}", expediente=expedientes[e], medico=medicos[m],
                       fecha=fecha, motivo=motivo, diagnostico=diag, tratamiento=trat,
                       observaciones=obs))

    # --- Algunas citas próximas ---
    base = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    for i, (p, m, motivo) in enumerate([
        (8, 0, "Chequeo general"), (9, 3, "Control de presión arterial"),
        (10, 2, "Primer control ginecológico"), (1, 3, "Control de hipertensión"),
        (3, 1, "Control de diabetes"),
    ], start=1):
        s.add(Cita(paciente=pacientes[p], medico=medicos[m], motivo=motivo,
                   fecha_hora=base + timedelta(days=i, hours=i % 4)))
    s.commit()
    return True
