# Archivo: vistas/p_inicio.py
# RF-12: panel general con indicadores y estadísticas de atención.
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
                               QVBoxLayout, QWidget)

from . import theme as T
from .pagina import Pagina
from .widgets import Card, PulsoECG, TarjetaDato, boton, celda, crear_tabla, etiqueta

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


class PaginaInicio(Pagina):
    ir_a = Signal(str)

    def __init__(self, ctx):
        super().__init__(ctx)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        # --- Banner de bienvenida ---
        banner = QFrame()
        banner.setMinimumHeight(138)
        banner.setStyleSheet(f"QFrame {{ border-radius: 18px; background: qlineargradient("
                             f"x1:0,y1:0,x2:1,y2:1, stop:0 {T.AZUL}, stop:1 {T.TEAL_CLARO}); }}"
                             "QLabel { background: transparent; color: white; }")
        b = QHBoxLayout(banner)
        b.setContentsMargins(30, 20, 30, 20)
        col = QVBoxLayout()
        col.setSpacing(4)
        self.lbl_saludo = QLabel()
        self.lbl_saludo.setStyleSheet("font-size: 21pt; font-weight: 800; color: white;")
        self.lbl_fecha = QLabel()
        self.lbl_fecha.setStyleSheet("font-size: 10.5pt; color: #D5EEF1;")
        col.addStretch()
        col.addWidget(self.lbl_saludo)
        col.addWidget(self.lbl_fecha)
        col.addStretch()
        b.addLayout(col, 3)
        pulso = PulsoECG("#FFFFFF")
        pulso.setMinimumHeight(90)
        b.addWidget(pulso, 2)
        lay.addWidget(banner)

        # --- Indicadores ---
        grid = QGridLayout()
        grid.setSpacing(16)
        defs = [("", "Pacientes registrados", "pacientes", T.TEAL),
                ("", "Expedientes clínicos", "expedientes", T.AZUL),
                ("", "Consultas registradas", "consultas", T.VERDE),
                ("", "Médicos activos", "medicos_activos", T.TEAL),
                ("", "Edad promedio (años)", "edad_promedio", T.AMBAR),
                ("", "IMC promedio", "imc_promedio", T.AZUL),
                ("", "Pacientes sin expediente", "sin_expediente", T.ROJO)]
        self.tarjetas: dict[str, TarjetaDato] = {}
        for i, (ic, tit, clave, col_) in enumerate(defs):
            t = TarjetaDato(ic, tit, col_)
            self.tarjetas[clave] = t
            grid.addWidget(t, i // 4, i % 4, Qt.AlignTop)
        # Accesos rápidos (según permisos)
        acc = Card(margen=16)
        acc.lay.addWidget(etiqueta("Accesos rápidos", "h3"))
        self.acc_lay = QVBoxLayout()
        self.acc_lay.setSpacing(8)
        acc.lay.addLayout(self.acc_lay)
        acc.lay.addStretch()
        grid.addWidget(acc, 1, 3, Qt.AlignTop)
        lay.addLayout(grid)

        # --- Tablas ---
        fila = QHBoxLayout()
        fila.setSpacing(16)
        c1 = Card()
        c1.lay.addWidget(etiqueta("Consultas registradas por médico", "h2"))
        self.tabla = crear_tabla(["Médico", "Especialidad", "Consultas"], expandir=0)
        c1.lay.addWidget(self.tabla)
        fila.addWidget(c1, 3)
        c2 = Card()
        c2.lay.addWidget(etiqueta("Diagnósticos más frecuentes", "h2"))
        self.diag_lay = QVBoxLayout()
        self.diag_lay.setSpacing(10)
        c2.lay.addLayout(self.diag_lay)
        c2.lay.addStretch()
        fila.addWidget(c2, 2)
        lay.addLayout(fila, 1)

        for texto, destino, permiso in (("Registrar paciente", "pacientes", "pacientes.editar"),
                                        ("Abrir expedientes", "expedientes", "expedientes.ver"),
                                        ("Programar cita", "citas", "citas.editar")):
            if self.puede(permiso):
                self.acc_lay.addWidget(boton(texto, "default", lambda _=False, d=destino: self.ir_a.emit(d)))

    def refrescar(self):
        u = self.ctx.sesion.usuario
        h = datetime.now()
        saludo = "Buenos días" if h.hour < 12 else "Buenas tardes" if h.hour < 19 else "Buenas noches"
        partes = u.nombre_completo.split(" ")
        nombre = " ".join(partes[:2]) if partes[0] in ("Dr.", "Dra.", "Enf.") else partes[0]
        self.lbl_saludo.setText(f"{saludo}, {nombre}")
        self.lbl_fecha.setText(f"{DIAS[h.weekday()].capitalize()}, {h.day} de {MESES[h.month - 1]} de {h.year}"
                               "  ·  Panel general del sistema")
        d = self.ctx.estadisticas.panel()
        for clave, t in self.tarjetas.items():
            t.set_valor(d[clave])
        self.tabla.setRowCount(len(d["por_medico"]))
        for i, (nombre, esp, n) in enumerate(d["por_medico"]):
            self.tabla.setItem(i, 0, celda(nombre, negrita=True))
            self.tabla.setItem(i, 1, celda(esp))
            self.tabla.setItem(i, 2, celda(n, centro=True, color=T.TEAL, negrita=True))
        while self.diag_lay.count():
            w = self.diag_lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        frecuentes = self.ctx.estadisticas.diagnosticos_frecuentes(6)
        tope = max((n for _d, n in frecuentes), default=1)
        for diag, n in frecuentes:
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(3)
            r = QHBoxLayout()
            r.addWidget(QLabel(diag), 1)
            num = QLabel(str(n))
            num.setStyleSheet(f"font-weight: 700; color: {T.TEAL};")
            r.addWidget(num)
            v.addLayout(r)
            pb = QProgressBar()
            pb.setRange(0, tope)
            pb.setValue(n)
            pb.setTextVisible(False)
            pb.setFixedHeight(8)
            v.addWidget(pb)
            self.diag_lay.addWidget(w)
