# Archivo: vistas/p_medicos.py
# RF-05: gestión de médicos y especialidades.
from __future__ import annotations

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout, QLineEdit, QTextEdit,
                               QVBoxLayout)

from . import theme as T
from .pagina import Pagina
from .widgets import (Card, aviso, boton, campo, celda, chip, confirmar, crear_tabla,
                      encabezado_pagina, error, etiqueta, exito, seleccionar_uid, uid_fila)


class DialogoEspecialidad(QDialog):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("Nueva especialidad")
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(8)
        lay.addWidget(etiqueta("Nueva especialidad médica", "h2"))
        self.txt_nombre = QLineEdit()
        self.txt_desc = QTextEdit(); self.txt_desc.setFixedHeight(80)
        for r, w in (("Nombre", self.txt_nombre), ("Descripción", self.txt_desc)):
            lay.addWidget(campo(r))
            lay.addWidget(w)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(boton("Cancelar", "ghost", self.reject))
        fila.addWidget(boton("Guardar", "primary", self._guardar))
        lay.addLayout(fila)

    def _guardar(self):
        try:
            self.ctx.medicos.crear_especialidad(self.txt_nombre.text(), self.txt_desc.toPlainText())
        except Exception as e:
            return error(self, e)
        self.accept()


class PaginaMedicos(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.id_sel: int | None = None
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(16)
        raiz.addWidget(encabezado_pagina("Médicos y especialidades", "Administre el personal médico disponible para citas y consultas.", ""))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        raiz.addLayout(cuerpo, 1)

        form = Card()
        form.setFixedWidth(380)
        self.lbl_titulo = etiqueta("Nuevo médico", "h2")
        form.lay.addWidget(self.lbl_titulo)
        self.txt_codigo = QLineEdit(); self.txt_codigo.setPlaceholderText("Ej: MED-005")
        self.txt_nombre = QLineEdit(); self.txt_nombre.setPlaceholderText("Nombre completo")
        self.cmb_esp = QComboBox()
        self.txt_tel = QLineEdit(); self.txt_tel.setPlaceholderText("Teléfono")
        self.chk_activo = QCheckBox("Médico activo"); self.chk_activo.setChecked(True)
        for r, w in (("Código", self.txt_codigo), ("Nombre completo", self.txt_nombre),
                     ("Especialidad", self.cmb_esp), ("Teléfono", self.txt_tel)):
            form.lay.addWidget(campo(r))
            form.lay.addWidget(w)
        form.lay.addWidget(self.chk_activo)
        self.btn_reg = boton("Registrar médico", "primary", self.registrar)
        self.btn_mod = boton("Modificar seleccionado", "warn", self.modificar)
        self.btn_baja = boton("Eliminar / desactivar", "danger", self.baja)
        for b in (self.btn_reg, self.btn_mod, self.btn_baja,
                  boton("Nueva especialidad", "default", self.nueva_especialidad),
                  boton("Limpiar", "ghost", self.limpiar)):
            form.lay.addWidget(b)
        form.lay.addStretch()
        cuerpo.addWidget(form)

        tab = Card()
        cab = QHBoxLayout()
        cab.addWidget(etiqueta("Personal médico", "h2"))
        self.chip_n = chip("0")
        cab.addWidget(self.chip_n)
        cab.addStretch()
        tab.lay.addLayout(cab)
        self.tabla = crear_tabla(["Código", "Nombre completo", "Especialidad", "Teléfono", "Estado"], expandir=1)
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        tab.lay.addWidget(self.tabla)
        tab.lay.addWidget(etiqueta("Si el médico ya tiene citas o consultas no se elimina: se desactiva para conservar el historial.", "muted"))
        cuerpo.addWidget(tab, 1)

    def refrescar(self):
        actual = self.cmb_esp.currentData()
        self.cmb_esp.clear()
        for e in self.ctx.medicos.especialidades():
            self.cmb_esp.addItem(e.nombre, e.id_especialidad)
        if actual is not None:
            self.cmb_esp.setCurrentIndex(max(self.cmb_esp.findData(actual), 0))
        lista = self.ctx.medicos.listar()
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(lista))
        for i, m in enumerate(lista):
            act = bool(m.activo)
            vals = [celda(m.codigo, uid=m.id_medico, negrita=True), celda(m.nombre_completo),
                    celda(m.especialidad.nombre), celda(m.telefono, True),
                    celda("Activo" if act else "Inactivo", True, T.VERDE if act else T.ROJO, True)]
            for c, it in enumerate(vals):
                self.tabla.setItem(i, c, it)
        self.tabla.blockSignals(False)
        self.chip_n.setText(f"{len(lista)}")
        if self.id_sel is not None and not seleccionar_uid(self.tabla, self.id_sel):
            self.limpiar()

    def _seleccion(self):
        uid = uid_fila(self.tabla)
        if uid is None:
            return
        from models import Medico
        m = self.ctx.db.session.get(Medico, uid)
        if m is None:
            return
        self.id_sel = m.id_medico
        self.lbl_titulo.setText(f"Editar médico · {m.codigo}")
        self.txt_codigo.setText(m.codigo)
        self.txt_codigo.setEnabled(False)
        self.txt_nombre.setText(m.nombre_completo)
        self.cmb_esp.setCurrentIndex(self.cmb_esp.findData(m.id_especialidad))
        self.txt_tel.setText(m.telefono)
        self.chk_activo.setChecked(bool(m.activo))

    def _leer(self) -> dict:
        return dict(codigo=self.txt_codigo.text(), nombre_completo=self.txt_nombre.text(),
                    id_especialidad=self.cmb_esp.currentData(), telefono=self.txt_tel.text(),
                    activo=self.chk_activo.isChecked())

    def limpiar(self):
        self.id_sel = None
        self.lbl_titulo.setText("Nuevo médico")
        for w in (self.txt_codigo, self.txt_nombre, self.txt_tel):
            w.clear()
        self.txt_codigo.setEnabled(True)
        self.chk_activo.setChecked(True)
        self.tabla.clearSelection()

    def registrar(self):
        if self.id_sel is not None:
            return aviso(self, "Hay un médico seleccionado. Pulse «Limpiar» para registrar uno nuevo.")
        try:
            self.ctx.medicos.crear(self._leer())
        except Exception as e:
            return error(self, e)
        exito(self, "Médico registrado correctamente.")
        self.limpiar()
        self.refrescar()

    def modificar(self):
        if self.id_sel is None:
            return aviso(self, "Seleccione un médico de la tabla.")
        try:
            self.ctx.medicos.actualizar(self.id_sel, self._leer())
        except Exception as e:
            return error(self, e)
        exito(self, "Datos del médico actualizados.")
        self.limpiar()
        self.refrescar()

    def baja(self):
        if self.id_sel is None:
            return aviso(self, "Seleccione un médico de la tabla.")
        if not confirmar(self, "¿Eliminar este médico? Si tiene citas o consultas se desactivará."):
            return
        try:
            r = self.ctx.medicos.eliminar_o_desactivar(self.id_sel)
        except Exception as e:
            return error(self, e)
        exito(self, f"Médico {r}.")
        self.limpiar()
        self.refrescar()

    def nueva_especialidad(self):
        if DialogoEspecialidad(self.ctx, self).exec() == QDialog.Accepted:
            self.refrescar()
