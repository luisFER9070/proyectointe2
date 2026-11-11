# Archivo: vistas/p_consultas.py
# RF-07 y RF-08: registro de consultas médicas e historial del expediente
# (siempre de la consulta más reciente a la más antigua).
from __future__ import annotations
 
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QComboBox, QCompleter, QDateEdit, QHBoxLayout, QLineEdit, QTextEdit,
                               QVBoxLayout)
 
from . import theme as T
from .pagina import Pagina
from .widgets import (Card, aviso, boton, campo, celda, chip, confirmar, crear_tabla,
                      encabezado_pagina, error, etiqueta, exito, fecha_txt, seleccionar_uid, uid_fila)
 
 
class PaginaConsultas(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.id_consulta: int | None = None
        self.editable = self.puede("consultas.registrar")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(14)
        raiz.addWidget(encabezado_pagina("Consultas médicas",
                       "Registre cada atención y revise el historial del expediente.", ""))
 
        # --- selector de expediente ---
        sel = Card(margen=14)
        fila = QHBoxLayout()
        fila.setSpacing(14)
        fila.addWidget(campo("Expediente"))
        self.cmb_exp = QComboBox()
        self.cmb_exp.setEditable(True)
        self.cmb_exp.setInsertPolicy(QComboBox.NoInsert)
        self.cmb_exp.setMinimumWidth(420)
        self.cmb_exp.currentIndexChanged.connect(self._cambio_expediente)
        fila.addWidget(self.cmb_exp)
        self.lbl_info = etiqueta("", "muted")
        fila.addWidget(self.lbl_info, 1)
        sel.lay.addLayout(fila)
        raiz.addWidget(sel)
 
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        raiz.addLayout(cuerpo, 1)
 
        # --- formulario ---
        form = Card()
        form.setFixedWidth(430)
        form.lay.setSpacing(4)
        form.lay.addWidget(etiqueta("Nueva consulta" if self.editable else "Detalle de la consulta", "h2"))
        if not self.editable:
            form.lay.addWidget(etiqueta("Modo consulta: su rol puede ver el historial pero no registrar consultas.", "aviso"))
        self.txt_codigo = QLineEdit(); self.txt_codigo.setReadOnly(True)
        self.fecha = QDateEdit(QDate.currentDate()); self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy"); self.fecha.setMaximumDate(QDate.currentDate())
        self.cmb_medico = QComboBox()
        self.cmb_cita = QComboBox()
        self.txt_motivo = QLineEdit(); self.txt_motivo.setPlaceholderText("Motivo de la consulta")
        self.txt_diag = QLineEdit(); self.txt_diag.setPlaceholderText("Diagnóstico")
        self.txt_trat = QTextEdit(); self.txt_trat.setFixedHeight(54)
        self.txt_trat.setPlaceholderText("Tratamiento indicado")
        self.txt_obs = QTextEdit(); self.txt_obs.setFixedHeight(54)
        self.txt_obs.setPlaceholderText("Observaciones")
        fr = QHBoxLayout()
        fr.setSpacing(10)
        for rotulo, w in (("Código", self.txt_codigo), ("Fecha", self.fecha)):
            c = QVBoxLayout(); c.setSpacing(3); c.addWidget(campo(rotulo)); c.addWidget(w); fr.addLayout(c)
        form.lay.addLayout(fr)
        for rotulo, w in (("Médico", self.cmb_medico), ("Cita de origen (opcional)", self.cmb_cita),
                          ("Motivo", self.txt_motivo), ("Diagnóstico", self.txt_diag),
                          ("Tratamiento", self.txt_trat), ("Observaciones", self.txt_obs)):
            form.lay.addWidget(campo(rotulo))
            form.lay.addWidget(w)
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btn_reg = boton("Registrar", "primary", self.registrar)
        self.btn_mod = boton("Modificar", "warn", self.modificar)
        self.btn_del = boton("Eliminar", "danger", self.eliminar)
        self.btn_lim = boton("Limpiar", "ghost", self.limpiar)
        for b in (self.btn_reg, self.btn_mod):
            botones.addWidget(b)
        form.lay.addLayout(botones)
        botones2 = QHBoxLayout()
        botones2.setSpacing(8)
        for b in (self.btn_del, self.btn_lim):
            botones2.addWidget(b)
        form.lay.addLayout(botones2)
        form.lay.addStretch()
        cuerpo.addWidget(form)
        if not self.editable:
            for w in (self.fecha, self.cmb_medico, self.cmb_cita, self.btn_reg, self.btn_mod, self.btn_del,
                      self.btn_lim):
                w.setEnabled(False)
            for w in (self.txt_motivo, self.txt_diag):
                w.setReadOnly(True)
            for w in (self.txt_trat, self.txt_obs):
                w.setReadOnly(True)
 
        # --- historial ---
        hist = Card()
        cab = QHBoxLayout()
        cab.addWidget(etiqueta("Historial del expediente", "h2"))
        self.chip_n = chip("0")
        cab.addWidget(self.chip_n)
        cab.addStretch()
        cab.addWidget(chip("Más reciente primero", T.MENTA, T.TEAL))
        hist.lay.addLayout(cab)
        self.tabla = crear_tabla(["Fecha", "Médico", "Diagnóstico"], expandir=2)
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        hist.lay.addWidget(self.tabla)
        cuerpo.addWidget(hist, 1)
 
    # ------------------------------------------------------------- datos ------
    def refrescar(self):
        actual = self.cmb_exp.currentData()
        self.cmb_exp.blockSignals(True)
        self.cmb_exp.clear()
        self.cmb_exp.addItem("— Seleccione un expediente —", None)
        for e in self.ctx.expedientes.listar() if self.puede("expedientes.ver") else []:
            self.cmb_exp.addItem(f"{e.numero}  ·  {e.paciente.nombre_completo}  ·  {e.paciente.cedula}",
                                 e.id_expediente)
        comp = QCompleter([self.cmb_exp.itemText(i) for i in range(self.cmb_exp.count())], self.cmb_exp)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)
        comp.popup().setStyleSheet(
            f"QListView {{ background: white; color: {T.TEXTO}; border: 1px solid {T.BORDE}; padding: 4px; }}"
            f"QListView::item {{ padding: 7px 10px; color: {T.TEXTO}; }}"
            f"QListView::item:selected {{ background: {T.MENTA}; color: {T.AZUL}; }}")
        self.cmb_exp.setCompleter(comp)
        self.cmb_medico.clear()
        for m in self.ctx.consultas.medicos_activos():
            self.cmb_medico.addItem(f"{m.nombre_completo} · {m.especialidad.nombre}", m.id_medico)
        propio = self.ctx.sesion.usuario.id_medico
        if propio:                                   # un médico registra con su propia identidad
            i = self.cmb_medico.findData(propio)
            if i >= 0:
                self.cmb_medico.setCurrentIndex(i)
            if self.editable:
                self.cmb_medico.setEnabled(False)
        if actual is not None:
            i = self.cmb_exp.findData(actual)
            self.cmb_exp.setCurrentIndex(max(i, 0))
        self.cmb_exp.blockSignals(False)
        self._cambio_expediente()
 
    def seleccionar_expediente(self, id_expediente: int):
        self.refrescar()
        i = self.cmb_exp.findData(id_expediente)
        if i >= 0:
            self.cmb_exp.setCurrentIndex(i)
 
    def _cambio_expediente(self):
        id_exp = self.cmb_exp.currentData()
        self.limpiar(recargar=False)
        self.tabla.setRowCount(0)
        self.chip_n.setText("0")
        self.cmb_cita.clear()
        self.cmb_cita.addItem("Sin cita asociada", None)
        if id_exp is None:
            self.lbl_info.setText("Elija un expediente para ver y registrar sus consultas.")
            return
        e = self.ctx.expedientes.obtener(id_exp)
        self.lbl_info.setText(f"{e.paciente.edad} años · {e.paciente.sexo} · Sangre {e.tipo_sangre} · "
                              f"Alergias: {e.alergias}")
        for c in self.ctx.consultas.citas_pendientes(id_exp):
            self.cmb_cita.addItem(f"{fecha_txt(c.fecha_hora)} · {c.medico.nombre_completo}", c.id_cita)
        self._cargar_historial()
 
    def _cargar_historial(self):
        id_exp = self.cmb_exp.currentData()
        if id_exp is None:
            return
        lista = self.ctx.consultas.historial(id_exp)              # más reciente primero
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(lista))
        for i, c in enumerate(lista):
            fondo = "#E8F6EE" if i == 0 else None
            vals = [celda(fecha_txt(c.fecha) + ("  ★" if i == 0 else ""), uid=c.id_consulta, negrita=True,
                          fondo=fondo, color=T.VERDE if i == 0 else None),
                    celda(c.medico.nombre_completo, fondo=fondo),
                    celda(c.diagnostico, negrita=True, fondo=fondo)]
            for col, it in enumerate(vals):
                self.tabla.setItem(i, col, it)
        self.tabla.blockSignals(False)
        self.chip_n.setText(f"{len(lista)} consulta{'s' if len(lista) != 1 else ''}")
        if self.id_consulta is not None:
            seleccionar_uid(self.tabla, self.id_consulta)
 
    # ------------------------------------------------------------ eventos -----
    def _seleccion(self):
        uid = uid_fila(self.tabla)
        if uid is None:
            return
        from models import Consulta
        c = self.ctx.db.session.get(Consulta, uid)
        if c is None:
            return
        self.id_consulta = c.id_consulta
        self.txt_codigo.setText(c.codigo)
        self.fecha.setDate(QDate(c.fecha.year, c.fecha.month, c.fecha.day))
        i = self.cmb_medico.findData(c.id_medico)
        if i >= 0:
            self.cmb_medico.setCurrentIndex(i)
        self.txt_motivo.setText(c.motivo)
        self.txt_diag.setText(c.diagnostico)
        self.txt_trat.setPlainText(c.tratamiento)
        self.txt_obs.setPlainText(c.observaciones)
        self.btn_reg.setEnabled(False)
 
    def limpiar(self, recargar: bool = True):
        self.id_consulta = None
        self.txt_codigo.setText(self.ctx.consultas.siguiente_codigo())
        self.fecha.setDate(QDate.currentDate())
        for w in (self.txt_motivo, self.txt_diag):
            w.clear()
        for w in (self.txt_trat, self.txt_obs):
            w.clear()
        self.cmb_cita.setCurrentIndex(0)
        self.btn_reg.setEnabled(self.editable)
        self.tabla.clearSelection()
 
    def _leer(self) -> dict:
        return dict(codigo=self.txt_codigo.text(), id_expediente=self.cmb_exp.currentData(),
                    id_medico=self.cmb_medico.currentData(), id_cita=self.cmb_cita.currentData(),
                    fecha=self.fecha.date().toPython(), motivo=self.txt_motivo.text(),
                    diagnostico=self.txt_diag.text(), tratamiento=self.txt_trat.toPlainText(),
                    observaciones=self.txt_obs.toPlainText())
 
    def _tras_cambio(self, mensaje: str):
        exito(self, mensaje)
        self.limpiar()
        self._cambio_expediente()
 
    def registrar(self):
        if self.cmb_exp.currentData() is None:
            return aviso(self, "Seleccione primero un expediente.")
        try:
            self.ctx.consultas.registrar(self._leer())
        except Exception as e:
            return error(self, e)
        self._tras_cambio("Consulta registrada y agregada al historial del paciente.")
 
    def modificar(self):
        if self.id_consulta is None:
            return aviso(self, "Seleccione una consulta del historial para modificarla.")
        try:
            self.ctx.consultas.actualizar(self.id_consulta, self._leer())
        except Exception as e:
            return error(self, e)
        self._tras_cambio("Consulta modificada correctamente.")
 
    def eliminar(self):
        if self.id_consulta is None:
            return aviso(self, "Seleccione la consulta que desea eliminar.")
        if not confirmar(self, f"¿Eliminar la consulta {self.txt_codigo.text()}? Esta acción no se puede deshacer."):
            return
        try:
            self.ctx.consultas.eliminar(self.id_consulta)
        except Exception as e:
            return error(self, e)
        self._tras_cambio("Consulta eliminada.")
 