# Archivo: vistas/p_citas.py
# RF-06: agenda de citas (programar, consultar y cancelar).
from __future__ import annotations

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QHBoxLayout, QLineEdit, QVBoxLayout

from . import theme as T
from .pagina import Pagina
from .widgets import (Card, aviso, boton, campo, celda, chip, confirmar, crear_tabla,
                      encabezado_pagina, error, etiqueta, exito, fecha_txt, uid_fila)

COLOR_ESTADO = {"programada": T.TEAL, "atendida": T.VERDE, "cancelada": T.ROJO}


class PaginaCitas(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.editable = self.puede("citas.editar")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(16)
        raiz.addWidget(encabezado_pagina("Agenda de citas", "Programe y controle las citas de pacientes con los médicos.", ""))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        raiz.addLayout(cuerpo, 1)

        form = Card()
        form.setFixedWidth(380)
        form.lay.addWidget(etiqueta("Programar cita", "h2"))
        self.cmb_pac = QComboBox()
        self.cmb_med = QComboBox()
        self.fecha = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy  HH:mm")
        self.txt_motivo = QLineEdit(); self.txt_motivo.setPlaceholderText("Motivo de la cita")
        for r, w in (("Paciente", self.cmb_pac), ("Médico", self.cmb_med), ("Fecha y hora", self.fecha),
                     ("Motivo", self.txt_motivo)):
            form.lay.addWidget(campo(r))
            form.lay.addWidget(w)
        self.btn_prog = boton("Programar cita", "primary", self.programar)
        self.btn_cancel = boton("Cancelar cita seleccionada", "danger", self.cancelar)
        form.lay.addWidget(self.btn_prog)
        form.lay.addWidget(self.btn_cancel)
        form.lay.addStretch()
        cuerpo.addWidget(form)
        if not self.editable:
            for w in (self.cmb_pac, self.cmb_med, self.fecha, self.txt_motivo, self.btn_prog, self.btn_cancel):
                w.setEnabled(False)

        tab = Card()
        cab = QHBoxLayout()
        cab.addWidget(etiqueta("Citas", "h2"))
        self.chip_n = chip("0")
        cab.addWidget(self.chip_n)
        cab.addStretch()
        self.f_med = QComboBox(); self.f_med.setMinimumWidth(240)
        self.f_est = QComboBox()
        self.f_est.addItem("Todos los estados", None)
        for e in ("programada", "atendida", "cancelada"):
            self.f_est.addItem(e.capitalize(), e)
        for w in (self.f_med, self.f_est):
            cab.addWidget(w)
            w.currentIndexChanged.connect(lambda _i: self.cargar())
        tab.lay.addLayout(cab)
        self.tabla = crear_tabla(["Fecha y hora", "Paciente", "Médico", "Motivo", "Estado"], expandir=3)
        tab.lay.addWidget(self.tabla)
        cuerpo.addWidget(tab, 1)

    def refrescar(self):
        for combo, items, todos in ((self.cmb_pac, [(f"{p.nombre_completo} · {p.cedula}", p.id_paciente)
                                                     for p in self.ctx.pacientes.listar()], None),
                                    (self.cmb_med, [(f"{m.nombre_completo} · {m.especialidad.nombre}", m.id_medico)
                                                     for m in self.ctx.consultas.medicos_activos()], None),
                                    (self.f_med, [(f"{m.nombre_completo}", m.id_medico)
                                                  for m in self.ctx.consultas.medicos_activos()], "Todos los médicos")):
            combo.blockSignals(True)
            combo.clear()
            if todos:
                combo.addItem(todos, None)
            for texto, dato in items:
                combo.addItem(texto, dato)
            combo.blockSignals(False)
        self.cargar()

    def cargar(self):
        try:
            lista = self.ctx.citas.listar(self.f_med.currentData(), self.f_est.currentData())
        except Exception as e:
            return error(self, e)
        self.tabla.setRowCount(len(lista))
        for i, c in enumerate(lista):
            col = COLOR_ESTADO[c.estado]
            vals = [celda(fecha_txt(c.fecha_hora), uid=c.id_cita, negrita=True), celda(c.paciente.nombre_completo),
                    celda(c.medico.nombre_completo), celda(c.motivo),
                    celda(c.estado.capitalize(), True, col, True)]
            for k, it in enumerate(vals):
                self.tabla.setItem(i, k, it)
        self.chip_n.setText(f"{len(lista)}")

    def programar(self):
        try:
            self.ctx.citas.programar(self.cmb_pac.currentData(), self.cmb_med.currentData(),
                                     self.fecha.dateTime().toPython(), self.txt_motivo.text())
        except Exception as e:
            return error(self, e)
        exito(self, "Cita programada correctamente.")
        self.txt_motivo.clear()
        self.cargar()

    def cancelar(self):
        uid = uid_fila(self.tabla)
        if uid is None:
            return aviso(self, "Seleccione la cita que desea cancelar.")
        if not confirmar(self, "¿Cancelar la cita seleccionada?"):
            return
        try:
            self.ctx.citas.cambiar_estado(uid, "cancelada")
        except Exception as e:
            return error(self, e)
        self.cargar()
