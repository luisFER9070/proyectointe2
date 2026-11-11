# Archivo: vistas/p_usuarios.py
# RF-09: administración de usuarios, roles y permisos.
# Desde aquí el administrador crea cuentas y decide qué puede hacer cada rol
# (doctor y enfermera) dentro del sistema.
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QTabWidget,
                               QVBoxLayout, QWidget)

from permisos import ETIQUETA_ROL, MATRIZ_POR_DEFECTO, PERMISOS
from . import theme as T
from .pagina import Pagina
from .widgets import (Card, Interruptor, aviso, boton, campo, celda, chip, confirmar, crear_tabla,
                      encabezado_pagina, error, etiqueta, exito, seleccionar_uid, uid_fila)

ROLES_ORDEN = ["admin", "doctor", "enfermera"]
MODULO = {c: m for c, _d, m in PERMISOS}


class PaginaUsuarios(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.id_sel: int | None = None
        self.sucio = False
        self.switches: dict[tuple[str, str], Interruptor] = {}
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(12)
        raiz.addWidget(encabezado_pagina("Usuarios y permisos",
                       "Cree cuentas de acceso y defina qué puede hacer cada rol en el sistema.", ""))
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_usuarios(), "Cuentas de usuario")
        self.tabs.addTab(self._tab_permisos(), "Permisos por rol")
        raiz.addWidget(self.tabs, 1)

    # =================== PESTAÑA 1: cuentas ===================
    def _tab_usuarios(self) -> QWidget:
        w = QWidget()
        cuerpo = QHBoxLayout(w)
        cuerpo.setContentsMargins(0, 8, 0, 0)
        cuerpo.setSpacing(18)
        form = Card()
        form.setFixedWidth(380)
        self.lbl_titulo = etiqueta("Nueva cuenta", "h2")
        form.lay.addWidget(self.lbl_titulo)
        self.txt_user = QLineEdit(); self.txt_user.setPlaceholderText("usuario")
        self.txt_nombre = QLineEdit(); self.txt_nombre.setPlaceholderText("Nombre completo")
        self.txt_clave = QLineEdit(); self.txt_clave.setEchoMode(QLineEdit.Password)
        self.txt_clave.setPlaceholderText("Mínimo 6 caracteres")
        self.cmb_rol = QComboBox()
        for r in ROLES_ORDEN:
            self.cmb_rol.addItem(ETIQUETA_ROL[r], r)
        self.cmb_rol.currentIndexChanged.connect(self._rol_cambio)
        self.cmb_medico = QComboBox()
        self.chk_activo = QCheckBox("Cuenta activa")
        self.chk_activo.setChecked(True)
        for r, x in (("Usuario", self.txt_user), ("Nombre completo", self.txt_nombre),
                     ("Contraseña", self.txt_clave), ("Rol", self.cmb_rol),
                     ("Médico asociado (solo rol médico)", self.cmb_medico)):
            form.lay.addWidget(campo(r))
            form.lay.addWidget(x)
        form.lay.addWidget(self.chk_activo)
        self.btn_crear = boton("Crear usuario", "primary", self.crear)
        self.btn_guardar = boton("Guardar cambios", "warn", self.guardar)
        self.btn_limpiar = boton("Limpiar", "ghost", self.limpiar)
        for b in (self.btn_crear, self.btn_guardar, self.btn_limpiar):
            form.lay.addWidget(b)
        form.lay.addStretch()
        cuerpo.addWidget(form)

        tab = Card()
        cab = QHBoxLayout()
        cab.addWidget(etiqueta("Cuentas registradas", "h2"))
        self.chip_n = chip("0")
        cab.addWidget(self.chip_n)
        cab.addStretch()
        tab.lay.addLayout(cab)
        self.tabla = crear_tabla(["Usuario", "Nombre completo", "Rol", "Médico asociado", "Estado"], expandir=1)
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        tab.lay.addWidget(self.tabla)
        tab.lay.addWidget(etiqueta("Las cuentas no se eliminan: se desactivan para conservar la trazabilidad.", "muted"))
        cuerpo.addWidget(tab, 1)
        return w

    def _rol_cambio(self):
        es_doctor = self.cmb_rol.currentData() == "doctor"
        self.cmb_medico.setEnabled(es_doctor)
        if not es_doctor:
            self.cmb_medico.setCurrentIndex(0)

    def _cargar_medicos(self):
        self.cmb_medico.clear()
        self.cmb_medico.addItem("— Sin médico asociado —", None)
        for m in self.ctx.usuarios.medicos_disponibles(self.id_sel):
            self.cmb_medico.addItem(f"{m.nombre_completo} · {m.especialidad.nombre}", m.id_medico)

    def cargar_usuarios(self):
        lista = self.ctx.usuarios.listar()
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(lista))
        for i, u in enumerate(lista):
            activo = bool(u.activo)
            vals = [celda(u.username, uid=u.id_usuario, negrita=True), celda(u.nombre_completo),
                    celda(ETIQUETA_ROL[u.rol.nombre], True, T.AZUL, True),
                    celda(u.medico.nombre_completo if u.medico else "—"),
                    celda("Activa" if activo else "Inactiva", True, T.VERDE if activo else T.ROJO, True)]
            for c, it in enumerate(vals):
                self.tabla.setItem(i, c, it)
        self.tabla.blockSignals(False)
        self.chip_n.setText(f"{len(lista)}")
        if self.id_sel is not None:
            seleccionar_uid(self.tabla, self.id_sel)

    def _seleccion(self):
        uid = uid_fila(self.tabla)
        if uid is None:
            return
        from models import Usuario
        u = self.ctx.db.session.get(Usuario, uid)
        if u is None:
            return
        self.id_sel = u.id_usuario
        self.lbl_titulo.setText(f"Editar cuenta · {u.username}")
        self._cargar_medicos()
        self.txt_user.setText(u.username)
        self.txt_user.setEnabled(False)
        self.txt_nombre.setText(u.nombre_completo)
        self.txt_clave.clear()
        self.txt_clave.setPlaceholderText("Dejar vacío para conservar la actual")
        self.cmb_rol.setCurrentIndex(self.cmb_rol.findData(u.rol.nombre))
        if u.id_medico:
            self.cmb_medico.addItem(f"{u.medico.nombre_completo} · {u.medico.especialidad.nombre}", u.id_medico)
            self.cmb_medico.setCurrentIndex(self.cmb_medico.findData(u.id_medico))
        self.chk_activo.setChecked(bool(u.activo))
        self.btn_crear.setEnabled(False)
        self.btn_guardar.setEnabled(True)

    def limpiar(self):
        self.id_sel = None
        self.lbl_titulo.setText("Nueva cuenta")
        for w in (self.txt_user, self.txt_nombre, self.txt_clave):
            w.clear()
        self.txt_user.setEnabled(True)
        self.txt_clave.setPlaceholderText("Mínimo 6 caracteres")
        self.cmb_rol.setCurrentIndex(0)
        self._cargar_medicos()
        self.chk_activo.setChecked(True)
        self.btn_crear.setEnabled(True)
        self.btn_guardar.setEnabled(False)
        self.tabla.clearSelection()
        self._rol_cambio()

    def crear(self):
        try:
            self.ctx.usuarios.crear(self.txt_user.text(), self.txt_nombre.text(), self.txt_clave.text(),
                                    self.cmb_rol.currentData(), self.cmb_medico.currentData(),
                                    self.chk_activo.isChecked())
        except Exception as e:
            return error(self, e)
        exito(self, "Usuario creado correctamente.")
        self.limpiar()
        self.cargar_usuarios()

    def guardar(self):
        if self.id_sel is None:
            return aviso(self, "Seleccione una cuenta de la tabla.")
        try:
            self.ctx.usuarios.actualizar(self.id_sel, self.txt_nombre.text(), self.cmb_rol.currentData(),
                                         self.cmb_medico.currentData(), self.chk_activo.isChecked(),
                                         self.txt_clave.text() or None)
        except Exception as e:
            return error(self, e)
        exito(self, "Cuenta actualizada correctamente.")
        self.limpiar()
        self.cargar_usuarios()

    # =================== PESTAÑA 2: permisos por rol ===================
    def _tab_permisos(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)
        card = Card()
        cab = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(etiqueta("Matriz de permisos por rol", "h2"))
        col.addWidget(etiqueta("Active o desactive lo que puede hacer el personal médico y de enfermería. "
                               "El administrador conserva siempre el control total.", "muted"))
        self.lbl_resumen = etiqueta("", "campo")
        col.addWidget(self.lbl_resumen)
        cab.addLayout(col, 1)
        self.chip_cambios = chip("Sin cambios pendientes", T.MENTA, T.MUTED)
        cab.addWidget(self.chip_cambios)
        card.lay.addLayout(cab)
        self.tabla_p = crear_tabla(["Funcionalidad", "Módulo", "Administrador", "Médico", "Enfermería"], expandir=0)
        self.tabla_p.verticalHeader().setDefaultSectionSize(50)
        self.tabla_p.setSelectionMode(QAbstractItemView.NoSelection)
        card.lay.addWidget(self.tabla_p, 1)
        pie = QHBoxLayout()
        pie.addStretch()
        pie.addWidget(boton("Restablecer a la matriz inicial", "ghost", self.restablecer))
        pie.addWidget(boton("Descartar cambios", "ghost", self.cargar_permisos))
        self.btn_guardar_p = boton("Guardar permisos", "primary", self.guardar_permisos)
        pie.addWidget(self.btn_guardar_p)
        card.lay.addLayout(pie)
        lay.addWidget(card, 1)
        return w

    def cargar_permisos(self):
        permisos, por_rol = self.ctx.usuarios.matriz_permisos()
        self.switches.clear()
        for cont in getattr(self, "_conts", []):
            cont.hide()
            cont.deleteLater()
        self._conts = []
        self.tabla_p.clearContents()
        self.tabla_p.setRowCount(len(permisos))
        for i, p in enumerate(permisos):
            item = celda(p.descripcion, negrita=True)
            self.tabla_p.setItem(i, 0, item)
            self.tabla_p.setItem(i, 1, celda(MODULO.get(p.clave, ""), True, T.MUTED))
            for j, rol in enumerate(ROLES_ORDEN):
                sw = Interruptor()
                sw.setChecked(p.clave in por_rol.get(rol, set()))
                if rol == "admin":
                    sw.setEnabled(False)
                    sw.setToolTip("Los permisos del administrador no se pueden modificar.")
                else:
                    sw.cambio.connect(lambda _v: self._marcar_sucio(True))
                self.switches[(rol, p.clave)] = sw
                cont = QWidget()
                h = QHBoxLayout(cont)
                h.setContentsMargins(0, 0, 0, 0)
                h.setAlignment(Qt.AlignCenter)
                h.addWidget(sw)
                self._conts.append(cont)
                self.tabla_p.setCellWidget(i, 2 + j, cont)
        self._marcar_sucio(False)

    def _marcar_sucio(self, pendiente: bool):
        self.sucio = pendiente
        if pendiente:
            self.chip_cambios.setText("● Cambios sin guardar")
            self.chip_cambios.setStyleSheet("background: #FDF0DA; color: #B8741A; border-radius: 11px; "
                                            "padding: 3px 12px; font-weight: 700; font-size: 9pt;")
        else:
            self.chip_cambios.setText("Sin cambios pendientes")
            self.chip_cambios.setStyleSheet(f"background: {T.MENTA}; color: {T.MUTED}; border-radius: 11px; "
                                            "padding: 3px 12px; font-weight: 700; font-size: 9pt;")
        total = len(PERMISOS)
        partes = [f"{ETIQUETA_ROL[r]}: {sum(1 for (rr, _c), s in self.switches.items() if rr == r and s.isChecked())}/{total}"
                  for r in ROLES_ORDEN]
        self.lbl_resumen.setText("Permisos activos  ·  " + "   |   ".join(partes))

    def _asignacion(self) -> dict[str, set[str]]:
        return {rol: {c for (r, c), s in self.switches.items() if r == rol and s.isChecked()}
                for rol in ("doctor", "enfermera")}

    def guardar_permisos(self):
        if not confirmar(self, "¿Guardar los permisos de Médico y Enfermería?\n\n"
                               "Los cambios se aplican en el siguiente inicio de sesión de cada usuario."):
            return
        try:
            self.ctx.usuarios.guardar_permisos(self._asignacion())
        except Exception as e:
            return error(self, e)
        exito(self, "Permisos guardados. Se aplicarán cuando cada usuario vuelva a iniciar sesión.")
        self.cargar_permisos()

    def restablecer(self):
        if not confirmar(self, "¿Restablecer los permisos de Médico y Enfermería a la matriz inicial del documento?"):
            return
        try:
            self.ctx.usuarios.restablecer_permisos()
        except Exception as e:
            return error(self, e)
        self.cargar_permisos()

    # ---------------------------------------------------------------------
    def refrescar(self):
        self.limpiar()
        self.cargar_usuarios()
        self.cargar_permisos()
