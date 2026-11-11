# Archivo: models.py
# Capa de Dominio + mapeo ORM (Proyecto Integrador II - UNAN-León)
# Sistema Gestor de Consultas y Expedientes de Pacientes
#
# Regla de arquitectura: este archivo NO importa nada de PySide6.
# Mapea con SQLAlchemy las 11 tablas del modelo relacional (Anexo C):
#   seguridad ........ roles, permisos, roles_permisos, usuarios, bitacora
#   personal médico .. especialidades, medicos
#   atención ......... pacientes, expedientes, citas, consultas
# Las reglas de negocio de la entidad (IMC, clasificación, última visita)
# viven aquí y nunca en la interfaz gráfica.
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric,
    String, Table, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ----------------------------- SEGURIDAD ------------------------------------
# Relación N:M entre roles y permisos (RBAC)
roles_permisos = Table(
    "roles_permisos", Base.metadata,
    Column("id_rol", ForeignKey("roles.id_rol", onupdate="CASCADE", ondelete="CASCADE"),
           primary_key=True),
    Column("id_permiso", ForeignKey("permisos.id_permiso", onupdate="CASCADE", ondelete="CASCADE"),
           primary_key=True),
)


class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = (CheckConstraint("nombre IN ('admin','doctor','enfermera')",
                                      name="chk_rol_nombre"),)
    id_rol: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str] = mapped_column(Text)
    permisos: Mapped[list[Permiso]] = relationship(secondary=roles_permisos, back_populates="roles")
    usuarios: Mapped[list[Usuario]] = relationship(back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"
    id_permiso: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(100), unique=True)   # ej: 'pacientes.editar'
    descripcion: Mapped[str] = mapped_column(Text)
    roles: Mapped[list[Rol]] = relationship(secondary=roles_permisos, back_populates="permisos")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (CheckConstraint("activo IN (0,1)", name="chk_usuario_activo"),)
    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    id_rol: Mapped[int] = mapped_column(ForeignKey("roles.id_rol", onupdate="CASCADE", ondelete="RESTRICT"))
    id_medico: Mapped[int | None] = mapped_column(
        ForeignKey("medicos.id_medico", onupdate="CASCADE", ondelete="SET NULL"), unique=True)
    activo: Mapped[int] = mapped_column(Integer, default=1)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    rol: Mapped[Rol] = relationship(back_populates="usuarios")
    medico: Mapped[Medico | None] = relationship(back_populates="usuario")


class Bitacora(Base):
    """Auditoría: quién hizo qué y cuándo."""
    __tablename__ = "bitacora"
    __table_args__ = (CheckConstraint(
        "accion IN ('LOGIN','LOGOUT','CREAR','MODIFICAR','ELIMINAR','EXPORTAR')",
        name="chk_bitacora_accion"),)
    id_bitacora: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="SET NULL"), index=True)
    accion: Mapped[str] = mapped_column(String(50))
    entidad: Mapped[str] = mapped_column(String(50))
    referencia: Mapped[str | None] = mapped_column(String(100))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    usuario: Mapped[Usuario | None] = relationship()


# --------------------------- PERSONAL MÉDICO --------------------------------
class Especialidad(Base):
    __tablename__ = "especialidades"
    id_especialidad: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str] = mapped_column(Text)
    medicos: Mapped[list[Medico]] = relationship(back_populates="especialidad")


class Medico(Base):
    __tablename__ = "medicos"
    __table_args__ = (CheckConstraint("activo IN (0,1)", name="chk_medico_activo"),)
    id_medico: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(150))
    id_especialidad: Mapped[int] = mapped_column(
        ForeignKey("especialidades.id_especialidad", onupdate="CASCADE", ondelete="RESTRICT"))
    telefono: Mapped[str] = mapped_column(String(30))
    activo: Mapped[int] = mapped_column(Integer, default=1)
    especialidad: Mapped[Especialidad] = relationship(back_populates="medicos")
    usuario: Mapped[Usuario | None] = relationship(back_populates="medico", uselist=False)
    citas: Mapped[list[Cita]] = relationship(back_populates="medico")
    consultas: Mapped[list[Consulta]] = relationship(back_populates="medico")


# ------------------------- PACIENTES Y EXPEDIENTES --------------------------
class Paciente(Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        CheckConstraint("edad BETWEEN 1 AND 120", name="chk_paciente_edad"),
        CheckConstraint("sexo IN ('Femenino','Masculino')", name="chk_paciente_sexo"),
        CheckConstraint("peso_kg BETWEEN 1.0 AND 400.0", name="chk_paciente_peso"),
        CheckConstraint("altura_m BETWEEN 0.30 AND 2.50", name="chk_paciente_altura"),
    )
    id_paciente: Mapped[int] = mapped_column(primary_key=True)
    cedula: Mapped[str] = mapped_column(String(50), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), index=True)
    edad: Mapped[int] = mapped_column(Integer)
    sexo: Mapped[str] = mapped_column(String(20))
    telefono: Mapped[str] = mapped_column(String(30))
    peso_kg: Mapped[float] = mapped_column(Numeric(5, 2, asdecimal=False))
    altura_m: Mapped[float] = mapped_column(Numeric(3, 2, asdecimal=False))
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expediente: Mapped[Expediente | None] = relationship(back_populates="paciente", uselist=False)
    citas: Mapped[list[Cita]] = relationship(back_populates="paciente")

    # --- Reglas de negocio (nunca en la interfaz gráfica) ---
    def calcular_imc(self) -> float:
        """IMC = peso (kg) / altura (m) al cuadrado."""
        if self.altura_m <= 0:
            raise ValueError("La altura debe ser mayor que cero para calcular el IMC.")
        return self.peso_kg / (self.altura_m ** 2)

    def clasificar_imc(self) -> str:
        imc = self.calcular_imc()
        if imc < 18.5:
            return "Bajo peso"
        if imc < 25:
            return "Normal"
        if imc < 30:
            return "Sobrepeso"
        return "Obesidad"


class Expediente(Base):
    __tablename__ = "expedientes"
    __table_args__ = (CheckConstraint(
        "tipo_sangre IN ('O+','O-','A+','A-','B+','B-','AB+','AB-')", name="chk_tipo_sangre"),)
    id_expediente: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True)
    id_paciente: Mapped[int] = mapped_column(      # UNIQUE fuerza la relación 1:1
        ForeignKey("pacientes.id_paciente", onupdate="CASCADE", ondelete="RESTRICT"), unique=True)
    tipo_sangre: Mapped[str] = mapped_column(String(10))
    alergias: Mapped[str] = mapped_column(Text)
    antecedentes: Mapped[str] = mapped_column(Text)
    fecha_apertura: Mapped[date] = mapped_column(Date, default=date.today)
    paciente: Mapped[Paciente] = relationship(back_populates="expediente")
    # Las consultas SIEMPRE salen de la más reciente a la más antigua.
    consultas: Mapped[list[Consulta]] = relationship(
        back_populates="expediente",
        order_by="[Consulta.fecha.desc(), Consulta.id_consulta.desc()]",
        cascade="all, delete-orphan", passive_deletes=True)

    @property
    def total_consultas(self) -> int:
        return len(self.consultas)

    @property
    def ultima_visita(self) -> date | None:
        return self.consultas[0].fecha if self.consultas else None


# ---------------------------- AGENDA Y CONSULTAS ----------------------------
class Cita(Base):
    __tablename__ = "citas"
    __table_args__ = (CheckConstraint("estado IN ('programada','atendida','cancelada')",
                                      name="chk_cita_estado"),)
    id_cita: Mapped[int] = mapped_column(primary_key=True)
    id_paciente: Mapped[int] = mapped_column(
        ForeignKey("pacientes.id_paciente", onupdate="CASCADE", ondelete="RESTRICT"), index=True)
    id_medico: Mapped[int] = mapped_column(
        ForeignKey("medicos.id_medico", onupdate="CASCADE", ondelete="RESTRICT"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime)
    motivo: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(30), default="programada")
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paciente: Mapped[Paciente] = relationship(back_populates="citas")
    medico: Mapped[Medico] = relationship(back_populates="citas")
    consulta: Mapped[Consulta | None] = relationship(back_populates="cita", uselist=False)


class Consulta(Base):
    __tablename__ = "consultas"
    id_consulta: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    id_expediente: Mapped[int] = mapped_column(
        ForeignKey("expedientes.id_expediente", onupdate="CASCADE", ondelete="CASCADE"), index=True)
    id_medico: Mapped[int] = mapped_column(
        ForeignKey("medicos.id_medico", onupdate="CASCADE", ondelete="RESTRICT"), index=True)
    id_cita: Mapped[int | None] = mapped_column(
        ForeignKey("citas.id_cita", onupdate="CASCADE", ondelete="SET NULL"), unique=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    motivo: Mapped[str] = mapped_column(Text)
    diagnostico: Mapped[str] = mapped_column(Text)
    tratamiento: Mapped[str] = mapped_column(Text)
    observaciones: Mapped[str] = mapped_column(Text)
    expediente: Mapped[Expediente] = relationship(back_populates="consultas")
    medico: Mapped[Medico] = relationship(back_populates="consultas")
    cita: Mapped[Cita | None] = relationship(back_populates="consulta")
