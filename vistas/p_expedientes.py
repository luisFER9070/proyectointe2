# Archivo: vistas/p_expedientes.py
# RF-03, RF-04 y RF-08: expedientes clínicos con el historial de consultas del
# paciente ordenado de la MÁS RECIENTE a la MÁS ANTIGUA.
from __future__ import annotations

from datetime import date
from html import escape

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QStackedWidget, QTextBrowser, QTextEdit, QVBoxLayout, QWidget)

from controller import TIPOS_SANGRE
from . import theme as T
from .pagina import Pagina
from .widgets import (Card, aviso, boton, campo, celda, chip, color_imc, crear_tabla,
                      encabezado_pagina, error, etiqueta, exito, fecha_txt, seleccionar_uid, uid_fila)


class DialogoExpediente(QDialog):
    """Apertura de un expediente para un paciente que aún no lo tiene (relación 1:1)."""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("Nuevo expediente clínico")
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(10)
        lay.addWidget(etiqueta("Abrir expediente clínico", "h2"))
        lay.addWidget(etiqueta("Cada paciente tiene un único expediente.", "muted"))
        self.sin_exp = ctx.expedientes.pacientes_sin_expediente()
        self.cmb_pac = QComboBox()
        for p in self.sin_exp:
            self.cmb_pac.addItem(f"{p.nombre_completo}  ·  {p.cedula}", p.id_paciente)
        self.txt_num = QLineEdit(ctx.expedientes.siguiente_numero())
        self.cmb_sangre = QComboBox()
        self.cmb_sangre.addItems(TIPOS_SANGRE)
        self.fecha = QDateEdit(QDate.currentDate())
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy")
        self.txt_alergias = QTextEdit(); self.txt_alergias.setFixedHeight(64)
        self.txt_alergias.setPlaceholderText("Ninguna conocida")
        self.txt_antec = QTextEdit(); self.txt_antec.setFixedHeight(64)
        self.txt_antec.setPlaceholderText("Antecedentes personales y familiares")
        f = QFormLayout()
        f.setVerticalSpacing(8)
        for r, w in (("Paciente", self.cmb_pac), ("N.º de expediente", self.txt_num),
                     ("Tipo de sangre", self.cmb_sangre), ("Fecha de apertura", self.fecha),
                     ("Alergias", self.txt_alergias), ("Antecedentes", self.txt_antec)):
            f.addRow(campo(r), w)
        lay.addLayout(f)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(boton("Cancelar", "ghost", self.reject))
        self.btn_ok = boton("Abrir expediente", "primary", self._aceptar)
        fila.addWidget(self.btn_ok)
        lay.addLayout(fila)
        if not self.sin_exp:
            self.btn_ok.setEnabled(False)
            lay.insertWidget(2, etiqueta("Todos los pacientes registrados ya tienen expediente.", "aviso"))

    def _aceptar(self):
        try:
            self.expediente = self.ctx.expedientes.crear(
                self.cmb_pac.currentData(), self.txt_num.text(), self.cmb_sangre.currentText(),
                self.txt_alergias.toPlainText(), self.txt_antec.toPlainText(),
                self.fecha.date().toPython())
        except Exception as e:
            return error(self, e)
        self.accept()


class PaginaExpedientes(Pagina):
    abrir_consulta = Signal(int)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.id_sel: int | None = None
        self.editable = self.puede("expedientes.editar")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(16)
        raiz.addWidget(encabezado_pagina(
            "Expedientes clínicos", "Busque un expediente y revise su ficha y todas sus consultas, "
            "de la más reciente a la más antigua.", ""))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        raiz.addLayout(cuerpo, 1)

        # ------------- lista de expedientes (izquierda) -------------
        lista = Card()
        lista.setFixedWidth(430)
        fila = QHBoxLayout()
        fila.addWidget(etiqueta("Expedientes", "h2"))
        self.chip_total = chip("0")
        fila.addWidget(self.chip_total)
        fila.addStretch()
        if self.editable:
            fila.addWidget(boton("Nuevo", "primary", self.nuevo))
        lista.lay.addLayout(fila)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Paciente, cédula o N.º de expediente…")
        self.txt_buscar.textChanged.connect(lambda _t: self.cargar_lista())
        lista.lay.addWidget(self.txt_buscar)
        self.tabla = crear_tabla(["N.º", "Paciente", "Visitas", "Última"], expandir=1)
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        lista.lay.addWidget(self.tabla)
        cuerpo.addWidget(lista)

        # ------------- detalle (derecha) -------------
        self.pila = QStackedWidget()
        vacio = Card()
        vacio.lay.addStretch()
        ic = QLabel("")
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("font-size: 54pt; background: transparent;")
        vacio.lay.addWidget(ic)
        t = etiqueta("Seleccione un expediente", "h2")
        t.setAlignment(Qt.AlignCenter)
        vacio.lay.addWidget(t)
        s = etiqueta("Aquí verá la ficha del paciente y su historial de consultas.", "muted")
        s.setAlignment(Qt.AlignCenter)
        vacio.lay.addWidget(s)
        vacio.lay.addStretch()
        self.pila.addWidget(vacio)
        self.pila.addWidget(self._construir_detalle())
        cuerpo.addWidget(self.pila, 1)

    def _construir_detalle(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        # --- ficha del paciente ---
        ficha = Card()
        cab = QHBoxLayout()
        cab.setSpacing(14)
        self.avatar = QLabel("?")
        self.avatar.setFixedSize(58, 58)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {T.TEAL_CLARO},"
                                  f"stop:1 {T.AZUL}); color: white; border-radius: 29px; "
                                  "font-size: 20pt; font-weight: 800;")
        cab.addWidget(self.avatar)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.lbl_nombre = etiqueta("", "h2")
        self.lbl_datos = etiqueta("", "muted")
        col.addWidget(self.lbl_nombre)
        col.addWidget(self.lbl_datos)
        cab.addLayout(col, 1)
        ficha.lay.addLayout(cab)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chip_exp = chip("")
        self.chip_sangre = chip("", "#FBE4E4", T.ROJO)
        self.chip_imc = chip("")
        for c_ in (self.chip_exp, self.chip_sangre, self.chip_imc):
            chips.addWidget(c_)
        chips.addStretch()
        ficha.lay.addLayout(chips)

        fila = QHBoxLayout()
        fila.setSpacing(14)
        c1 = QVBoxLayout()
        c1.addWidget(campo("Tipo de sangre"))
        self.cmb_sangre = QComboBox()
        self.cmb_sangre.addItems(TIPOS_SANGRE)
        c1.addWidget(self.cmb_sangre)
        c1.addStretch()
        fila.addLayout(c1)
        c2 = QVBoxLayout()
        c2.addWidget(campo("Alergias"))
        self.txt_alergias = QTextEdit(); self.txt_alergias.setFixedHeight(64)
        c2.addWidget(self.txt_alergias)
        fila.addLayout(c2, 1)
        c3 = QVBoxLayout()
        c3.addWidget(campo("Antecedentes"))
        self.txt_antec = QTextEdit(); self.txt_antec.setFixedHeight(64)
        c3.addWidget(self.txt_antec)
        fila.addLayout(c3, 1)
        ficha.lay.addLayout(fila)
        acciones = QHBoxLayout()
        acciones.addStretch()
        self.btn_guardar = boton("Guardar cambios", "primary", self.guardar)
        self.btn_nueva = boton("Registrar consulta", "default",
                               lambda: self.abrir_consulta.emit(self.id_sel))
        if self.puede("consultas.registrar"):
            acciones.addWidget(self.btn_nueva)
        if self.editable:
            acciones.addWidget(self.btn_guardar)
        else:
            for x in (self.cmb_sangre,):
                x.setEnabled(False)
            self.txt_alergias.setReadOnly(True)
            self.txt_antec.setReadOnly(True)
        ficha.lay.addLayout(acciones)
        lay.addWidget(ficha)

        # --- historial ---
        hist = Card()
        cab2 = QHBoxLayout()
        cab2.addWidget(etiqueta("Historial de consultas", "h2"))
        self.chip_n = chip("0")
        cab2.addWidget(self.chip_n)
        cab2.addStretch()
        cab2.addWidget(chip("Más reciente primero", T.MENTA, T.TEAL))
        hist.lay.addLayout(cab2)
        self.tabla_h = crear_tabla(["Fecha", "Médico", "Diagnóstico"],
                                   expandir=2)
        self.tabla_h.setMinimumHeight(140)
        self.tabla_h.itemSelectionChanged.connect(self._ver_consulta)
        hist.lay.addWidget(self.tabla_h, 1)
        self.detalle = QTextBrowser()
        self.detalle.setFixedHeight(156)
        hist.lay.addWidget(self.detalle)
        lay.addWidget(hist, 1)
        return w

    # ------------------------------------------------------------- datos -------
    def refrescar(self):
        self.cargar_lista()

    def seleccionar(self, id_expediente: int):
        self.txt_buscar.clear()
        self.cargar_lista()
        seleccionar_uid(self.tabla, id_expediente)

    def cargar_lista(self):
        try:
            lista = self.ctx.expedientes.listar(self.txt_buscar.text())
        except Exception as e:
            return error(self, e)
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(lista))
        for i, e in enumerate(lista):
            vals = [celda(e.numero, uid=e.id_expediente, negrita=True),
                    celda(f"{e.paciente.nombre_completo}"), celda(e.total_consultas, True), celda(fecha_txt(e.ultima_visita), True)]
            for c, it in enumerate(vals):
                self.tabla.setItem(i, c, it)
        self.tabla.blockSignals(False)
        self.chip_total.setText(f"{len(lista)}")
        if self.id_sel is not None and seleccionar_uid(self.tabla, self.id_sel):
            self._mostrar(self.id_sel)
        else:
            self.id_sel = None
            self.pila.setCurrentIndex(0)

    def _seleccion(self):
        uid = uid_fila(self.tabla)
        if uid is not None:
            self._mostrar(uid)

    def _mostrar(self, id_expediente: int):
        e = self.ctx.expedientes.obtener(id_expediente)
        if e is None:
            return
        self.id_sel = id_expediente
        p = e.paciente
        self.avatar.setText(p.nombre_completo[:1].upper())
        self.lbl_nombre.setText(p.nombre_completo)
        self.lbl_datos.setText(f"Cédula {p.cedula}  ·  {p.edad} años  ·  {p.sexo}  ·  Tel. {p.telefono}")
        self.chip_exp.setText(f"{e.numero} · apertura {fecha_txt(e.fecha_apertura)}")
        self.chip_sangre.setText(f"{e.tipo_sangre}")
        clasif = p.clasificar_imc()
        col = color_imc(clasif)
        self.chip_imc.setText(f"IMC {p.calcular_imc():.1f} · {clasif}")
        self.chip_imc.setStyleSheet(f"background: {T.suave(col)}; color: {col}; border-radius: 11px; "
                                    "padding: 3px 12px; font-weight: 700; font-size: 9pt;")
        self.cmb_sangre.setCurrentText(e.tipo_sangre)
        self.txt_alergias.setPlainText(e.alergias)
        self.txt_antec.setPlainText(e.antecedentes)
        self._cargar_historial(e.id_expediente)
        self.pila.setCurrentIndex(1)

    def _cargar_historial(self, id_expediente: int):
        # El controlador entrega las consultas de la más reciente a la más antigua.
        consultas = self.ctx.consultas.historial(id_expediente) if self.puede("consultas.ver") else []
        self.tabla_h.blockSignals(True)
        self.tabla_h.setRowCount(len(consultas))
        for i, c in enumerate(consultas):
            reciente = i == 0
            fondo = "#E8F6EE" if reciente else None
            f = fecha_txt(c.fecha) + ("  ★" if reciente else "")
            vals = [celda(f, uid=c.id_consulta, negrita=True, fondo=fondo, color=T.VERDE if reciente else None),
                    celda(c.medico.nombre_completo, fondo=fondo),
                    celda(c.diagnostico, negrita=True, fondo=fondo)]
            for col_, it in enumerate(vals):
                self.tabla_h.setItem(i, col_, it)
        self.tabla_h.blockSignals(False)
        self.chip_n.setText(f"{len(consultas)} consulta{'s' if len(consultas) != 1 else ''}")
        if consultas:
            self.tabla_h.selectRow(0)
        else:
            self.detalle.setHtml(f"<p style='color:{T.MUTED}'>Este paciente aún no tiene consultas registradas.</p>")

    def _ver_consulta(self):
        uid = uid_fila(self.tabla_h)
        if uid is None:
            return
        from models import Consulta
        c = self.ctx.db.session.get(Consulta, uid)
        if c is None:
            return
        def fila(rotulo, texto):
            return (f"<tr><td style='color:{T.MUTED}; padding:2px 14px 2px 0; white-space:nowrap;'><b>{rotulo}</b></td>"
                    f"<td style='padding:2px 0;'>{escape(texto)}</td></tr>")
        self.detalle.setHtml(
            f"<div style='font-size:10pt'><b style='color:{T.AZUL}; font-size:11pt'>{escape(c.codigo)}</b> "
            f"<span style='color:{T.MUTED}'>· {fecha_txt(c.fecha)} · {escape(c.medico.nombre_completo)} "
            f"({escape(c.medico.especialidad.nombre)})</span>"
            f"<table>{fila('Motivo', c.motivo)}{fila('Diagnóstico', c.diagnostico)}"
            f"{fila('Tratamiento', c.tratamiento)}{fila('Observaciones', c.observaciones)}</table></div>")

    # ------------------------------------------------------------ acciones -----
    def nuevo(self):
        d = DialogoExpediente(self.ctx, self)
        if d.exec() == QDialog.Accepted:
            self.txt_buscar.clear()
            self.id_sel = d.expediente.id_expediente
            self.cargar_lista()
            exito(self, f"Expediente {d.expediente.numero} abierto correctamente.")

    def guardar(self):
        if self.id_sel is None:
            return aviso(self, "Seleccione un expediente.")
        try:
            self.ctx.expedientes.actualizar(self.id_sel, self.cmb_sangre.currentText(),
                                            self.txt_alergias.toPlainText(), self.txt_antec.toPlainText())
        except Exception as e:
            return error(self, e)
        exito(self, "Expediente actualizado correctamente.")
        self.cargar_lista()
