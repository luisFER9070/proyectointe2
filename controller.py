# Archivo: controller.py
# Capa de Lógica de Negocio (Proyecto Integrador II - UNAN-León)
# Sistema Gestor de Consultas y Expedientes de Pacientes
#
# Centraliza validaciones, control de acceso por roles (RBAC), operaciones CRUD y
# la bitácora de auditoría. NO contiene código visual: la interfaz solo llama a
# estos controladores (criterio de desacoplamiento de la guía de sesión 13).
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from models import (Bitacora, Cita, Consulta, Especialidad, Expediente, Medico,
                    Paciente, Permiso, Rol, Usuario)
from permisos import MATRIZ_POR_DEFECTO, PERMISOS
from security import hash_password, verify_password

TIPOS_SANGRE = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
ACCIONES_BITACORA = ["LOGIN", "LOGOUT", "CREAR", "MODIFICAR", "ELIMINAR", "EXPORTAR"]


class PermisoDenegado(PermissionError):
    """El rol del usuario en sesión no tiene el permiso requerido."""


# ------------------------------------------------------------------ SESIÓN ---
class Sesion:
    """Usuario autenticado y los permisos que su rol tiene en este momento."""

    def __init__(self):
        self.usuario: Usuario | None = None
        self.permisos: frozenset[str] = frozenset()

    @property
    def activa(self) -> bool:
        return self.usuario is not None

    @property
    def rol(self) -> str:
        return self.usuario.rol.nombre if self.usuario else ""

    def abrir(self, usuario: Usuario):
        self.usuario = usuario
        self.recargar()

    def recargar(self):
        claves = {p.clave for p in self.usuario.rol.permisos}
        if self.rol == "admin":              # el admin nunca puede quedarse sin gestión de usuarios
            claves.add("usuarios.gestionar")
        self.permisos = frozenset(claves)

    def cerrar(self):
        self.usuario = None
        self.permisos = frozenset()

    def puede(self, clave: str) -> bool:
        return clave in self.permisos

    def exigir(self, clave: str):
        if not self.puede(clave):
            raise PermisoDenegado("Su rol no tiene permiso para realizar esta acción.")


class _Base:
    def __init__(self, db, sesion: Sesion):
        self.db = db
        self.s = db.session
        self.sesion = sesion

    def _log(self, accion: str, entidad: str, referencia: str | None = None):
        """Agrega el evento a la bitácora dentro de la misma transacción."""
        uid = self.sesion.usuario.id_usuario if self.sesion.usuario else None
        self.s.add(Bitacora(id_usuario=uid, accion=accion, entidad=entidad,
                            referencia=(referencia or "")[:100] or None))

    def _commit(self):
        try:
            self.s.commit()
        except IntegrityError as e:
            self.s.rollback()
            raise ValueError("No se pudo guardar: el dato ya existe o viola una regla de integridad.") from e
        except Exception:
            self.s.rollback()
            raise

    @staticmethod
    def _texto(valor, campo: str) -> str:
        v = str(valor or "").strip()
        if not v:
            raise ValueError(f"El campo «{campo}» es obligatorio.")
        return v


# --------------------------------------------------------------------- AUTH ---
class AuthController(_Base):
    def iniciar_sesion(self, username: str, password: str) -> Usuario:
        if not username.strip() or not password:
            raise ValueError("Ingrese su usuario y contraseña.")
        u = self.s.scalar(select(Usuario).where(Usuario.username == username.strip()))
        if u is None or not u.activo or not verify_password(password, u.password_hash):
            raise ValueError("Credenciales inválidas o usuario inactivo.")
        self.sesion.abrir(u)
        self._log("LOGIN", "usuarios", u.username)
        self._commit()
        return u

    def cerrar_sesion(self):
        if self.sesion.activa:
            self._log("LOGOUT", "usuarios", self.sesion.usuario.username)
            self._commit()
        self.sesion.cerrar()


# ---------------------------------------------------------------- PACIENTES ---
class PacienteController(_Base):
    def listar(self, texto: str = "") -> list[Paciente]:
        self.sesion.exigir("pacientes.ver")
        q = select(Paciente)
        t = texto.strip()
        if t:
            like = f"%{t}%"
            q = q.where(or_(Paciente.nombre_completo.ilike(like), Paciente.cedula.ilike(like)))
        return list(self.s.scalars(q.order_by(Paciente.nombre_completo)))

    def obtener(self, id_paciente: int) -> Paciente | None:
        return self.s.get(Paciente, id_paciente)

    @staticmethod
    def _validar(d: dict) -> dict:
        cedula = str(d.get("cedula", "")).strip()
        nombre = str(d.get("nombre_completo", "")).strip()
        telefono = str(d.get("telefono", "")).strip()
        sexo = str(d.get("sexo", "")).strip()
        if not (cedula and nombre and telefono and sexo):
            raise ValueError("Complete todos los campos obligatorios del formulario.")
        try:
            edad = int(str(d.get("edad", "")).strip())
            peso = float(str(d.get("peso_kg", "")).replace(",", ".").strip())
            altura = float(str(d.get("altura_m", "")).replace(",", ".").strip())
        except ValueError:
            raise ValueError("Edad, peso y altura deben ser valores numéricos.")
        if not 1 <= edad <= 120:
            raise ValueError("La edad debe estar entre 1 y 120 años.")
        if sexo not in ("Femenino", "Masculino"):
            raise ValueError("El sexo debe ser Femenino o Masculino.")
        if not 1 <= peso <= 400:
            raise ValueError("El peso debe estar entre 1 y 400 kg.")
        if not 0.30 <= altura <= 2.50:
            raise ValueError("La altura debe estar entre 0.30 y 2.50 m.")
        return dict(cedula=cedula, nombre_completo=nombre, edad=edad, sexo=sexo,
                    telefono=telefono, peso_kg=peso, altura_m=altura)

    def crear(self, datos: dict) -> Paciente:
        self.sesion.exigir("pacientes.editar")
        v = self._validar(datos)
        if self.s.scalar(select(Paciente).where(Paciente.cedula == v["cedula"])):
            raise ValueError(f"La cédula «{v['cedula']}» ya está registrada en el sistema.")
        p = Paciente(**v)
        self.s.add(p)
        self._log("CREAR", "pacientes", p.cedula)
        self._commit()
        return p

    def actualizar(self, id_paciente: int, datos: dict) -> Paciente:
        self.sesion.exigir("pacientes.editar")
        p = self.s.get(Paciente, id_paciente)
        if p is None:
            raise ValueError("El paciente que intenta actualizar no existe.")
        v = self._validar({**datos, "cedula": p.cedula})      # la cédula no se modifica
        for k, val in v.items():
            setattr(p, k, val)
        self._log("MODIFICAR", "pacientes", p.cedula)
        self._commit()
        return p

    def eliminar(self, id_paciente: int):
        self.sesion.exigir("pacientes.editar")
        p = self.s.get(Paciente, id_paciente)
        if p is None:
            raise ValueError("El paciente a eliminar no existe.")
        if p.expediente is not None or p.citas:
            raise ValueError("No se puede dar de baja: el paciente tiene expediente o citas asociadas.")
        cedula = p.cedula
        self.s.delete(p)
        self._log("ELIMINAR", "pacientes", cedula)
        self._commit()


# -------------------------------------------------------------- EXPEDIENTES ---
class ExpedienteController(_Base):
    def listar(self, texto: str = "") -> list[Expediente]:
        self.sesion.exigir("expedientes.ver")
        q = select(Expediente).join(Paciente)
        t = texto.strip()
        if t:
            like = f"%{t}%"
            q = q.where(or_(Paciente.nombre_completo.ilike(like), Paciente.cedula.ilike(like),
                            Expediente.numero.ilike(like)))
        return list(self.s.scalars(q.order_by(Paciente.nombre_completo)))

    def obtener(self, id_expediente: int) -> Expediente | None:
        return self.s.get(Expediente, id_expediente)

    def pacientes_sin_expediente(self) -> list[Paciente]:
        q = select(Paciente).outerjoin(Expediente).where(Expediente.id_expediente.is_(None))
        return list(self.s.scalars(q.order_by(Paciente.nombre_completo)))

    def siguiente_numero(self) -> str:
        n = (self.s.scalar(select(func.max(Expediente.id_expediente))) or 0) + 1
        while self.s.scalar(select(Expediente).where(Expediente.numero == f"EXP-{n:04d}")):
            n += 1
        return f"EXP-{n:04d}"

    def crear(self, id_paciente: int, numero: str, tipo_sangre: str, alergias: str,
              antecedentes: str, fecha_apertura: date | None = None) -> Expediente:
        self.sesion.exigir("expedientes.editar")
        p = self.s.get(Paciente, id_paciente)
        if p is None:
            raise ValueError("Seleccione un paciente válido.")
        if p.expediente is not None:
            raise ValueError("El paciente ya tiene un expediente (relación 1:1).")
        if tipo_sangre not in TIPOS_SANGRE:
            raise ValueError("Tipo de sangre no válido.")
        numero = self._texto(numero, "Número de expediente")
        if self.s.scalar(select(Expediente).where(Expediente.numero == numero)):
            raise ValueError("El número de expediente ya existe.")
        e = Expediente(numero=numero, paciente=p, tipo_sangre=tipo_sangre,
                       alergias=alergias.strip() or "Ninguna conocida",
                       antecedentes=antecedentes.strip() or "Sin antecedentes registrados",
                       fecha_apertura=fecha_apertura or date.today())
        self.s.add(e)
        self._log("CREAR", "expedientes", numero)
        self._commit()
        return e

    def actualizar(self, id_expediente: int, tipo_sangre: str, alergias: str, antecedentes: str):
        self.sesion.exigir("expedientes.editar")
        e = self.s.get(Expediente, id_expediente)
        if e is None:
            raise ValueError("El expediente no existe.")
        if tipo_sangre not in TIPOS_SANGRE:
            raise ValueError("Tipo de sangre no válido.")
        e.tipo_sangre = tipo_sangre
        e.alergias = alergias.strip() or "Ninguna conocida"
        e.antecedentes = antecedentes.strip() or "Sin antecedentes registrados"
        self._log("MODIFICAR", "expedientes", e.numero)
        self._commit()
        return e


# ----------------------------------------------------------------- CONSULTAS ---
class ConsultaController(_Base):
    def historial(self, id_expediente: int, desde: date | None = None,
                  hasta: date | None = None) -> list[Consulta]:
        """Consultas del expediente, de la MÁS RECIENTE a la MÁS ANTIGUA (RF-08)."""
        self.sesion.exigir("consultas.ver")
        q = select(Consulta).where(Consulta.id_expediente == id_expediente)
        if desde:
            q = q.where(Consulta.fecha >= desde)
        if hasta:
            q = q.where(Consulta.fecha <= hasta)
        return list(self.s.scalars(q.order_by(Consulta.fecha.desc(), Consulta.id_consulta.desc())))

    def siguiente_codigo(self) -> str:
        n = (self.s.scalar(select(func.max(Consulta.id_consulta))) or 0) + 1
        while self.s.scalar(select(Consulta).where(Consulta.codigo == f"CON-{n:04d}")):
            n += 1
        return f"CON-{n:04d}"

    def medicos_activos(self) -> list[Medico]:
        return list(self.s.scalars(select(Medico).where(Medico.activo == 1)
                                   .order_by(Medico.nombre_completo)))

    def citas_pendientes(self, id_expediente: int) -> list[Cita]:
        e = self.s.get(Expediente, id_expediente)
        if e is None:
            return []
        q = (select(Cita).where(Cita.id_paciente == e.id_paciente, Cita.estado == "programada")
             .order_by(Cita.fecha_hora))
        return [c for c in self.s.scalars(q) if c.consulta is None]

    def _validar(self, d: dict) -> dict:
        e = self.s.get(Expediente, d.get("id_expediente"))
        if e is None:
            raise ValueError("Seleccione un expediente.")
        m = self.s.get(Medico, d.get("id_medico"))
        if m is None or not m.activo:
            raise ValueError("Seleccione un médico activo.")
        if not isinstance(d.get("fecha"), date):
            raise ValueError("La fecha de la consulta no es válida.")
        if d["fecha"] > date.today():
            raise ValueError("La fecha de la consulta no puede ser futura.")
        return dict(expediente=e, medico=m, fecha=d["fecha"],
                    motivo=self._texto(d.get("motivo"), "Motivo"),
                    diagnostico=self._texto(d.get("diagnostico"), "Diagnóstico"),
                    tratamiento=self._texto(d.get("tratamiento"), "Tratamiento"),
                    observaciones=str(d.get("observaciones", "")).strip() or "Sin observaciones")

    def registrar(self, d: dict) -> Consulta:
        self.sesion.exigir("consultas.registrar")
        v = self._validar(d)
        codigo = self._texto(d.get("codigo"), "Código")
        if self.s.scalar(select(Consulta).where(Consulta.codigo == codigo)):
            raise ValueError("El código de consulta ya existe.")
        cita = None
        if d.get("id_cita"):
            cita = self.s.get(Cita, d["id_cita"])
            if cita is None or cita.consulta is not None:
                raise ValueError("La cita seleccionada no está disponible.")
        c = Consulta(codigo=codigo, cita=cita, **v)
        if cita is not None:
            cita.estado = "atendida"
        self.s.add(c)
        self._log("CREAR", "consultas", codigo)
        self._commit()
        return c

    def actualizar(self, id_consulta: int, d: dict) -> Consulta:
        self.sesion.exigir("consultas.registrar")
        c = self.s.get(Consulta, id_consulta)
        if c is None:
            raise ValueError("La consulta no existe.")
        v = self._validar({**d, "id_expediente": c.id_expediente})
        for k in ("medico", "fecha", "motivo", "diagnostico", "tratamiento", "observaciones"):
            setattr(c, k, v[k])
        self._log("MODIFICAR", "consultas", c.codigo)
        self._commit()
        return c

    def eliminar(self, id_consulta: int):
        self.sesion.exigir("consultas.registrar")
        c = self.s.get(Consulta, id_consulta)
        if c is None:
            raise ValueError("La consulta no existe.")
        codigo = c.codigo
        if c.cita is not None:
            c.cita.estado = "programada"
        self.s.delete(c)
        self._log("ELIMINAR", "consultas", codigo)
        self._commit()


# -------------------------------------------------------------------- CITAS ---
class CitaController(_Base):
    def listar(self, id_medico: int | None = None, estado: str | None = None) -> list[Cita]:
        self.sesion.exigir("citas.ver")
        q = select(Cita)
        if id_medico:
            q = q.where(Cita.id_medico == id_medico)
        if estado:
            q = q.where(Cita.estado == estado)
        return list(self.s.scalars(q.order_by(Cita.fecha_hora.desc())))

    def programar(self, id_paciente: int, id_medico: int, fecha_hora: datetime, motivo: str) -> Cita:
        self.sesion.exigir("citas.editar")
        p = self.s.get(Paciente, id_paciente)
        m = self.s.get(Medico, id_medico)
        if p is None:
            raise ValueError("Seleccione un paciente.")
        if m is None or not m.activo:
            raise ValueError("Seleccione un médico activo.")
        if fecha_hora < datetime.now() - timedelta(minutes=1):
            raise ValueError("La cita no puede programarse en una fecha pasada.")
        motivo = self._texto(motivo, "Motivo")
        choque = self.s.scalar(select(Cita).where(
            Cita.id_medico == id_medico, Cita.fecha_hora == fecha_hora, Cita.estado != "cancelada"))
        if choque is not None:
            raise ValueError("El médico ya tiene una cita en esa fecha y hora.")
        c = Cita(paciente=p, medico=m, fecha_hora=fecha_hora, motivo=motivo, estado="programada")
        self.s.add(c)
        self._log("CREAR", "citas", f"{p.cedula} {fecha_hora:%d/%m/%Y %H:%M}")
        self._commit()
        return c

    def cambiar_estado(self, id_cita: int, estado: str):
        self.sesion.exigir("citas.editar")
        c = self.s.get(Cita, id_cita)
        if c is None:
            raise ValueError("La cita no existe.")
        if c.estado == "atendida":
            raise ValueError("Una cita atendida no puede modificarse.")
        c.estado = estado
        self._log("MODIFICAR", "citas", f"{c.paciente.cedula} → {estado}")
        self._commit()


# ------------------------------------------------------------------ MÉDICOS ---
class MedicoController(_Base):
    def listar(self) -> list[Medico]:
        self.sesion.exigir("medicos.gestionar")
        return list(self.s.scalars(select(Medico).order_by(Medico.nombre_completo)))

    def especialidades(self) -> list[Especialidad]:
        return list(self.s.scalars(select(Especialidad).order_by(Especialidad.nombre)))

    def _validar(self, d: dict) -> dict:
        esp = self.s.get(Especialidad, d.get("id_especialidad"))
        if esp is None:
            raise ValueError("Seleccione una especialidad.")
        return dict(codigo=self._texto(d.get("codigo"), "Código"),
                    nombre_completo=self._texto(d.get("nombre_completo"), "Nombre completo"),
                    telefono=self._texto(d.get("telefono"), "Teléfono"),
                    especialidad=esp, activo=1 if d.get("activo", True) else 0)

    def crear(self, d: dict) -> Medico:
        self.sesion.exigir("medicos.gestionar")
        v = self._validar(d)
        if self.s.scalar(select(Medico).where(Medico.codigo == v["codigo"])):
            raise ValueError("El código del médico ya existe.")
        m = Medico(**v)
        self.s.add(m)
        self._log("CREAR", "medicos", m.codigo)
        self._commit()
        return m

    def actualizar(self, id_medico: int, d: dict) -> Medico:
        self.sesion.exigir("medicos.gestionar")
        m = self.s.get(Medico, id_medico)
        if m is None:
            raise ValueError("El médico no existe.")
        v = self._validar({**d, "codigo": m.codigo})
        for k, val in v.items():
            setattr(m, k, val)
        self._log("MODIFICAR", "medicos", m.codigo)
        self._commit()
        return m

    def eliminar_o_desactivar(self, id_medico: int) -> str:
        """Si tiene citas o consultas se desactiva para conservar el historial."""
        self.sesion.exigir("medicos.gestionar")
        m = self.s.get(Medico, id_medico)
        if m is None:
            raise ValueError("El médico no existe.")
        if m.citas or m.consultas:
            m.activo = 0
            self._log("MODIFICAR", "medicos", f"{m.codigo} desactivado")
            self._commit()
            return "desactivado"
        codigo = m.codigo
        self.s.delete(m)
        self._log("ELIMINAR", "medicos", codigo)
        self._commit()
        return "eliminado"

    def crear_especialidad(self, nombre: str, descripcion: str) -> Especialidad:
        self.sesion.exigir("medicos.gestionar")
        nombre = self._texto(nombre, "Nombre de la especialidad")
        if self.s.scalar(select(Especialidad).where(Especialidad.nombre == nombre)):
            raise ValueError("La especialidad ya existe.")
        e = Especialidad(nombre=nombre, descripcion=descripcion.strip() or "Sin descripción")
        self.s.add(e)
        self._log("CREAR", "especialidades", nombre)
        self._commit()
        return e


# ------------------------------------------------- USUARIOS, ROLES Y PERMISOS ---
class UsuarioController(_Base):
    def listar(self) -> list[Usuario]:
        self.sesion.exigir("usuarios.gestionar")
        return list(self.s.scalars(select(Usuario).order_by(Usuario.username)))

    def roles(self) -> list[Rol]:
        return list(self.s.scalars(select(Rol).order_by(Rol.id_rol)))

    def medicos_disponibles(self, id_usuario: int | None = None) -> list[Medico]:
        """Médicos activos que aún no tienen cuenta (o la del usuario editado)."""
        ocupados = select(Usuario.id_medico).where(Usuario.id_medico.is_not(None))
        if id_usuario:
            ocupados = ocupados.where(Usuario.id_usuario != id_usuario)
        q = select(Medico).where(Medico.activo == 1, Medico.id_medico.not_in(ocupados))
        return list(self.s.scalars(q.order_by(Medico.nombre_completo)))

    def _rol(self, nombre: str) -> Rol:
        r = self.s.scalar(select(Rol).where(Rol.nombre == nombre))
        if r is None:
            raise ValueError("Rol no válido (admin, doctor o enfermera).")
        return r

    def crear(self, username, nombre_completo, password, rol, id_medico=None, activo=True) -> Usuario:
        self.sesion.exigir("usuarios.gestionar")
        username = self._texto(username, "Usuario")
        if self.s.scalar(select(Usuario).where(Usuario.username == username)):
            raise ValueError("El nombre de usuario ya existe.")
        if len(password or "") < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        u = Usuario(username=username, nombre_completo=self._texto(nombre_completo, "Nombre completo"),
                    password_hash=hash_password(password), rol=self._rol(rol),
                    id_medico=id_medico if rol == "doctor" else None, activo=1 if activo else 0)
        self.s.add(u)
        self._log("CREAR", "usuarios", username)
        self._commit()
        return u

    def actualizar(self, id_usuario, nombre_completo, rol, id_medico=None, activo=True,
                   password: str | None = None) -> Usuario:
        self.sesion.exigir("usuarios.gestionar")
        u = self.s.get(Usuario, id_usuario)
        if u is None:
            raise ValueError("El usuario no existe.")
        if u.id_usuario == self.sesion.usuario.id_usuario and (rol != "admin" or not activo):
            raise ValueError("No puede quitarse su propio rol de administrador ni desactivar su cuenta.")
        u.nombre_completo = self._texto(nombre_completo, "Nombre completo")
        u.rol = self._rol(rol)
        u.id_medico = id_medico if rol == "doctor" else None
        u.activo = 1 if activo else 0
        if password:
            if len(password) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres.")
            u.password_hash = hash_password(password)
        self._log("MODIFICAR", "usuarios", u.username)
        self._commit()
        return u

    # --- Asignación de permisos por rol (RF-09) ---
    def matriz_permisos(self) -> tuple[list[Permiso], dict[str, set[str]]]:
        self.sesion.exigir("usuarios.gestionar")
        orden = {c: i for i, (c, _d, _m) in enumerate(PERMISOS)}
        permisos = sorted(self.s.scalars(select(Permiso)), key=lambda p: orden.get(p.clave, 99))
        por_rol = {r.nombre: {p.clave for p in r.permisos} for r in self.roles()}
        return permisos, por_rol

    def guardar_permisos(self, asignacion: dict[str, set[str]]):
        """asignacion = {'doctor': {claves...}, 'enfermera': {claves...}}"""
        self.sesion.exigir("usuarios.gestionar")
        todos = {p.clave: p for p in self.s.scalars(select(Permiso))}
        for rol_nombre, claves in asignacion.items():
            if rol_nombre == "admin":
                raise ValueError("Los permisos del administrador no se pueden modificar.")
            rol = self._rol(rol_nombre)
            antes = {p.clave for p in rol.permisos}
            rol.permisos = [todos[c] for c in claves if c in todos]
            if antes != set(claves):
                self._log("MODIFICAR", "roles_permisos",
                          f"{rol_nombre}: +{len(set(claves) - antes)} -{len(antes - set(claves))}")
        self._commit()

    def restablecer_permisos(self):
        """Devuelve doctor y enfermera a la matriz inicial del documento (Tabla 10)."""
        self.guardar_permisos({r: set(MATRIZ_POR_DEFECTO[r]) for r in ("doctor", "enfermera")})


# ----------------------------------------------------------------- BITÁCORA ---
class BitacoraController(_Base):
    def listar(self, id_usuario: int | None = None, accion: str | None = None,
               desde: date | None = None, hasta: date | None = None, limite: int = 500):
        self.sesion.exigir("bitacora.ver")
        q = select(Bitacora)
        if id_usuario:
            q = q.where(Bitacora.id_usuario == id_usuario)
        if accion:
            q = q.where(Bitacora.accion == accion)
        if desde:
            q = q.where(Bitacora.fecha_hora >= datetime.combine(desde, datetime.min.time()))
        if hasta:
            q = q.where(Bitacora.fecha_hora < datetime.combine(hasta + timedelta(days=1), datetime.min.time()))
        return list(self.s.scalars(q.order_by(Bitacora.fecha_hora.desc(), Bitacora.id_bitacora.desc())
                                   .limit(limite)))

    def usuarios(self) -> list[Usuario]:
        return list(self.s.scalars(select(Usuario).order_by(Usuario.username)))


# ------------------------------------------------------------- ESTADÍSTICAS ---
class EstadisticasController(_Base):
    def panel(self) -> dict:
        self.sesion.exigir("panel.ver")
        s = self.s
        pacientes = list(s.scalars(select(Paciente)))
        imcs = [p.calcular_imc() for p in pacientes]
        sin_exp = s.scalar(select(func.count()).select_from(Paciente).outerjoin(Expediente)
                           .where(Expediente.id_expediente.is_(None)))
        n_consultas = func.count(Consulta.id_consulta)
        por_medico = s.execute(
            select(Medico.nombre_completo, Especialidad.nombre, n_consultas)
            .join(Especialidad).outerjoin(Consulta).where(Medico.activo == 1)
            .group_by(Medico.id_medico, Medico.nombre_completo, Especialidad.nombre)
            .order_by(n_consultas.desc(), Medico.nombre_completo)).all()
        return {
            "pacientes": len(pacientes),
            "expedientes": s.scalar(select(func.count()).select_from(Expediente)),
            "consultas": s.scalar(select(func.count()).select_from(Consulta)),
            "medicos_activos": s.scalar(select(func.count()).select_from(Medico).where(Medico.activo == 1)),
            "edad_promedio": round(sum(p.edad for p in pacientes) / len(pacientes)) if pacientes else 0,
            "imc_promedio": round(sum(imcs) / len(imcs), 1) if imcs else 0.0,
            "sin_expediente": sin_exp,
            "citas_pendientes": s.scalar(select(func.count()).select_from(Cita)
                                         .where(Cita.estado == "programada", Cita.fecha_hora >= datetime.now())),
            "por_medico": [(n, e, c) for n, e, c in por_medico],
        }

    def diagnosticos_frecuentes(self, limite: int = 8) -> list[tuple[str, int]]:
        total = func.count(Consulta.id_consulta)
        filas = self.s.execute(select(Consulta.diagnostico, total).group_by(Consulta.diagnostico)
                               .order_by(total.desc(), Consulta.diagnostico).limit(limite)).all()
        return [(d, n) for d, n in filas]


# ----------------------------------------------------------------- CONTEXTO ---
class Contexto:
    """Reúne la sesión y todos los controladores que la interfaz necesita."""

    def __init__(self, db):
        self.db = db
        self.sesion = Sesion()
        self.auth = AuthController(db, self.sesion)
        self.pacientes = PacienteController(db, self.sesion)
        self.expedientes = ExpedienteController(db, self.sesion)
        self.consultas = ConsultaController(db, self.sesion)
        self.citas = CitaController(db, self.sesion)
        self.medicos = MedicoController(db, self.sesion)
        self.usuarios = UsuarioController(db, self.sesion)
        self.bitacora = BitacoraController(db, self.sesion)
        self.estadisticas = EstadisticasController(db, self.sesion)
        from reportes_pdf import ReporteController      # import tardío: reportlab solo si se usa
        self.reportes = ReporteController(db, self.sesion)
