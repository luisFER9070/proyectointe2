# Archivo: vistas/p_reportes.py
# RF-11: reportes en PDF y diagnósticos más frecuentes.
from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QFileDialog, QHBoxLayout, QLabel,
                               QMessageBox, QVBoxLayout)

from . import theme as T
from .pagina import Pagina
from .widgets import Card, aviso, boton, campo, celda, crear_tabla, encabezado_pagina, error, etiqueta


class PaginaReportes(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(16)
        raiz.addWidget(encabezado_pagina("Reportes y estadísticas", "Exporte la información del sistema en PDF con plantilla institucional.", ""))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        raiz.addLayout(cuerpo, 1)

        col = QVBoxLayout()
        col.setSpacing(16)
        cuerpo.addLayout(col, 3)
        # 1) pacientes
        c1 = Card()
        c1.lay.addWidget(etiqueta("Listado de pacientes", "h2"))
        c1.lay.addWidget(etiqueta("Todos los pacientes con sus datos, IMC y número de expediente.", "muted"))
        c1.lay.addWidget(boton("Exportar reporte de pacientes", "primary", self.rep_pacientes))
        col.addWidget(c1)
        # 2) expediente
        c2 = Card()
        c2.lay.addWidget(etiqueta("Expediente de un paciente", "h2"))
        c2.lay.addWidget(etiqueta("Ficha clínica y consultas, de la más reciente a la más antigua.", "muted"))
        self.cmb_exp = QComboBox()
        c2.lay.addWidget(self.cmb_exp)
        c2.lay.addWidget(boton("Exportar expediente", "primary", self.rep_expediente))
        col.addWidget(c2)
        # 3) consultas
        c3 = Card()
        c3.lay.addWidget(etiqueta("Consultas por médico y fechas", "h2"))
        self.cmb_med = QComboBox()
        c3.lay.addWidget(self.cmb_med)
        fila = QHBoxLayout()
        self.chk = QCheckBox("Filtrar por fechas")
        self.d1 = QDateEdit(QDate.currentDate().addMonths(-3)); self.d2 = QDateEdit(QDate.currentDate())
        for d in (self.d1, self.d2):
            d.setCalendarPopup(True); d.setDisplayFormat("dd/MM/yyyy"); d.setEnabled(False)
        self.chk.toggled.connect(lambda v: [d.setEnabled(v) for d in (self.d1, self.d2)])
        for w in (self.chk, self.d1, self.d2):
            fila.addWidget(w)
        c3.lay.addLayout(fila)
        c3.lay.addWidget(boton("Exportar reporte de consultas", "primary", self.rep_consultas))
        col.addWidget(c3)
        col.addStretch()

        c4 = Card()
        c4.lay.addWidget(etiqueta("Diagnósticos más frecuentes", "h2"))
        self.tabla = crear_tabla(["Diagnóstico", "Casos"], expandir=0)
        c4.lay.addWidget(self.tabla)
        cuerpo.addWidget(c4, 2)

    def refrescar(self):
        self.cmb_exp.clear()
        for e in self.ctx.expedientes.listar() if self.puede("expedientes.ver") else []:
            self.cmb_exp.addItem(f"{e.numero} · {e.paciente.nombre_completo}", e.id_expediente)
        self.cmb_med.clear()
        self.cmb_med.addItem("Todos los médicos", None)
        for m in self.ctx.consultas.medicos_activos():
            self.cmb_med.addItem(m.nombre_completo, m.id_medico)
        datos = self.ctx.estadisticas.diagnosticos_frecuentes(12) if self.puede("panel.ver") else []
        self.tabla.setRowCount(len(datos))
        for i, (d, n) in enumerate(datos):
            self.tabla.setItem(i, 0, celda(d, negrita=True))
            self.tabla.setItem(i, 1, celda(n, True, T.TEAL, True))

    def _ruta(self, nombre: str) -> str | None:
        base = str(Path.home() / f"{nombre}_{date.today():%Y%m%d}.pdf")
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar reporte PDF", base, "Documentos PDF (*.pdf)")
        return ruta or None

    def _terminado(self, ruta: str):
        r = QMessageBox.question(self, "Reporte generado", f"El reporte se guardó en:\n{ruta}\n\n¿Desea abrirlo ahora?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if r == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))

    def _generar(self, nombre, funcion):
        ruta = self._ruta(nombre)
        if not ruta:
            return
        try:
            self._terminado(funcion(ruta))
        except Exception as e:
            error(self, e)

    def rep_pacientes(self):
        self._generar("reporte_pacientes", self.ctx.reportes.pacientes)

    def rep_expediente(self):
        if self.cmb_exp.currentData() is None:
            return aviso(self, "Seleccione un expediente.")
        self._generar("expediente", lambda r: self.ctx.reportes.expediente(r, self.cmb_exp.currentData()))

    def rep_consultas(self):
        d1 = self.d1.date().toPython() if self.chk.isChecked() else None
        d2 = self.d2.date().toPython() if self.chk.isChecked() else None
        self._generar("reporte_consultas", lambda r: self.ctx.reportes.consultas(r, self.cmb_med.currentData(), d1, d2))
