# Archivo: vistas/p_bitacora.py
# RF-10: bitácora de auditoría (solo administrador).
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCheckBox, QComboBox, QDateEdit, QHBoxLayout, QVBoxLayout

from controller import ACCIONES_BITACORA
from . import theme as T
from .pagina import Pagina
from .widgets import Card, boton, celda, chip, crear_tabla, encabezado_pagina, error, etiqueta, fecha_txt

COLOR = {"LOGIN": T.VERDE, "LOGOUT": T.MUTED, "CREAR": T.TEAL, "MODIFICAR": T.AMBAR,
         "ELIMINAR": T.ROJO, "EXPORTAR": T.AZUL}


class PaginaBitacora(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(16)
        raiz.addWidget(encabezado_pagina("Bitácora de auditoría", "Quién hizo qué y cuándo: trazabilidad de la información.", ""))
        card = Card()
        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.cmb_user = QComboBox(); self.cmb_user.setMinimumWidth(180)
        self.cmb_accion = QComboBox()
        self.cmb_accion.addItem("Todas las acciones", None)
        for a in ACCIONES_BITACORA:
            self.cmb_accion.addItem(a, a)
        self.chk_fechas = QCheckBox("Filtrar por fecha")
        self.d_desde = QDateEdit(QDate.currentDate().addMonths(-1)); self.d_hasta = QDateEdit(QDate.currentDate())
        for d in (self.d_desde, self.d_hasta):
            d.setCalendarPopup(True)
            d.setDisplayFormat("dd/MM/yyyy")
            d.setEnabled(False)
        self.chk_fechas.toggled.connect(lambda v: [d.setEnabled(v) for d in (self.d_desde, self.d_hasta)])
        for w in (self.cmb_user, self.cmb_accion, self.chk_fechas, self.d_desde, self.d_hasta):
            fila.addWidget(w)
        fila.addStretch()
        self.chip_n = chip("0")
        fila.addWidget(self.chip_n)
        fila.addWidget(boton("Filtrar", "primary", self.cargar))
        card.lay.addLayout(fila)
        self.tabla = crear_tabla(["Fecha y hora", "Usuario", "Acción", "Entidad", "Referencia"], expandir=4)
        card.lay.addWidget(self.tabla)
        raiz.addWidget(card, 1)

    def refrescar(self):
        self.cmb_user.blockSignals(True)
        self.cmb_user.clear()
        self.cmb_user.addItem("Todos los usuarios", None)
        for u in self.ctx.bitacora.usuarios():
            self.cmb_user.addItem(u.username, u.id_usuario)
        self.cmb_user.blockSignals(False)
        self.cargar()

    def cargar(self):
        desde = self.d_desde.date().toPython() if self.chk_fechas.isChecked() else None
        hasta = self.d_hasta.date().toPython() if self.chk_fechas.isChecked() else None
        try:
            lista = self.ctx.bitacora.listar(self.cmb_user.currentData(), self.cmb_accion.currentData(), desde, hasta)
        except Exception as e:
            return error(self, e)
        self.tabla.setRowCount(len(lista))
        for i, b in enumerate(lista):
            vals = [celda(fecha_txt(b.fecha_hora), negrita=True),
                    celda(b.usuario.username if b.usuario else "(eliminado)"),
                    celda(b.accion, True, COLOR.get(b.accion), True), celda(b.entidad, True),
                    celda(b.referencia or "—")]
            for c, it in enumerate(vals):
                self.tabla.setItem(i, c, it)
        self.chip_n.setText(f"{len(lista)} eventos")
