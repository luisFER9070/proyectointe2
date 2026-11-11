# Archivo: vistas/p_pacientes.py
# RF-02 y RF-03: registro, modificación, baja y búsqueda de pacientes.
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout)

from models import Paciente
from . import theme as T
from .pagina import Pagina
from .widgets import (Card, aviso, boton, campo, celda, chip, color_imc, confirmar, crear_tabla,
                      encabezado_pagina, error, etiqueta, exito, seleccionar_uid, uid_fila)


class PaginaPacientes(Pagina):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.id_sel: int | None = None
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(16)
        raiz.addWidget(encabezado_pagina("Pacientes", "Registro, consulta y actualización de los datos de cada paciente.", ""))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        raiz.addLayout(cuerpo, 1)

        # ---------------- formulario ----------------
        form_card = Card()
        form_card.setFixedWidth(312)
        self.lbl_modo = etiqueta("", "aviso")
        self.lbl_modo.setWordWrap(True)
        form_card.lay.addWidget(etiqueta("Datos del paciente", "h2"))
        form_card.lay.addWidget(self.lbl_modo)
        f = QFormLayout()
        f.setVerticalSpacing(3)
        f.setRowWrapPolicy(QFormLayout.WrapAllRows)
        f.setLabelAlignment(Qt.AlignLeft)
        f.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.txt_cedula = QLineEdit(); self.txt_cedula.setPlaceholderText("Ej: 001-120395-0001A")
        self.txt_nombre = QLineEdit(); self.txt_nombre.setPlaceholderText("Nombre completo del paciente")
        self.txt_edad = QLineEdit(); self.txt_edad.setPlaceholderText("Años (1 – 120)")
        self.cmb_sexo = QComboBox(); self.cmb_sexo.addItems(["Femenino", "Masculino"])
        self.txt_tel = QLineEdit(); self.txt_tel.setPlaceholderText("Ej: 8801-1001")
        self.txt_peso = QLineEdit(); self.txt_peso.setPlaceholderText("Peso en kg")
        self.txt_altura = QLineEdit(); self.txt_altura.setPlaceholderText("Altura en m (Ej: 1.70)")
        for rotulo, w in (("Cédula / Carnet único", self.txt_cedula), ("Nombre completo", self.txt_nombre),
                          ("Edad", self.txt_edad), ("Sexo", self.cmb_sexo), ("Teléfono", self.txt_tel),
                          ("Peso (kg)", self.txt_peso), ("Altura (m)", self.txt_altura)):
            f.addRow(campo(rotulo), w)
        form_card.lay.addLayout(f)
        fila_imc = QHBoxLayout()
        fila_imc.addWidget(campo("IMC calculado"))
        self.lbl_imc = chip("—", T.MENTA, T.MUTED)
        fila_imc.addStretch()
        fila_imc.addWidget(self.lbl_imc)
        form_card.lay.addLayout(fila_imc)
        for w in (self.txt_peso, self.txt_altura):
            w.textChanged.connect(self._actualizar_imc)
        self.btn_guardar = boton("Registrar paciente", "primary", self.guardar)
        self.btn_mod = boton("Modificar seleccionado", "warn", self.modificar)
        self.btn_baja = boton("Dar de baja paciente", "danger", self.eliminar)
        self.btn_limpiar = boton("Limpiar formulario", "ghost", self.limpiar)
        for b in (self.btn_guardar, self.btn_mod, self.btn_baja, self.btn_limpiar):
            form_card.lay.addWidget(b)
        form_card.lay.addStretch()
        cuerpo.addWidget(form_card)

        # ---------------- tabla ----------------
        tabla_card = Card()
        barra = QHBoxLayout()
        barra.addWidget(etiqueta("Pacientes registrados", "h2"))
        self.chip_total = chip("0")
        barra.addWidget(self.chip_total)
        barra.addStretch()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por cédula o nombre…")
        self.txt_buscar.setFixedWidth(260)
        self.txt_buscar.textChanged.connect(lambda _t: self.cargar_tabla())
        barra.addWidget(self.txt_buscar)
        tabla_card.lay.addLayout(barra)
        self.tabla = crear_tabla(["Cédula", "Nombre completo", "Edad", "Peso kg", "Altura m", "IMC",
                                  "Estado"], expandir=1)
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        tabla_card.lay.addWidget(self.tabla)
        cuerpo.addWidget(tabla_card, 1)

        # permisos: la enfermera y el admin editan; el doctor solo consulta
        self.editable = self.puede("pacientes.editar")
        if not self.editable:
            self.lbl_modo.setText("Modo consulta: su rol puede ver los datos de los pacientes pero no modificarlos.")
            for w in (self.txt_cedula, self.txt_nombre, self.txt_edad, self.cmb_sexo, self.txt_tel,
                      self.txt_peso, self.txt_altura, self.btn_guardar, self.btn_mod, self.btn_baja,
                      self.btn_limpiar):
                w.setEnabled(False)
        else:
            self.lbl_modo.setText("Seleccione una fila para modificarla o darla de baja.")

    # ------------------------------------------------------------ datos -------
    def refrescar(self):
        self.cargar_tabla()

    def cargar_tabla(self):
        try:
            lista = self.ctx.pacientes.listar(self.txt_buscar.text())
        except Exception as e:
            return error(self, e)
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(lista))
        for i, p in enumerate(lista):
            clasif = p.clasificar_imc()
            vals = [celda(p.cedula, uid=p.id_paciente, negrita=True), celda(p.nombre_completo),
                    celda(p.edad, True),
                    celda(f"{p.peso_kg:.1f}", True), celda(f"{p.altura_m:.2f}", True),
                    celda(f"{p.calcular_imc():.1f}", True),
                    celda(clasif, True, color_imc(clasif), True)]
            for c, it in enumerate(vals):
                self.tabla.setItem(i, c, it)
        self.tabla.blockSignals(False)
        self.chip_total.setText(f"{len(lista)} paciente{'s' if len(lista) != 1 else ''}")
        if self.id_sel is not None and not seleccionar_uid(self.tabla, self.id_sel):
            self.limpiar()

    # ------------------------------------------------------------ eventos -----
    def _actualizar_imc(self):
        try:
            p = Paciente(peso_kg=float(self.txt_peso.text().replace(",", ".")),
                         altura_m=float(self.txt_altura.text().replace(",", ".")))
            clasif = p.clasificar_imc()
            self.lbl_imc.setText(f"{p.calcular_imc():.1f} · {clasif}")
            col = color_imc(clasif)
            self.lbl_imc.setStyleSheet(f"background: {T.suave(col)}; color: {col}; border-radius: 11px; "
                                       f"padding: 3px 12px; font-weight: 700; font-size: 9pt;")
        except (ValueError, ZeroDivisionError):
            self.lbl_imc.setText("—")
            self.lbl_imc.setStyleSheet(f"background: {T.MENTA}; color: {T.MUTED}; border-radius: 11px; "
                                       f"padding: 3px 12px; font-weight: 700; font-size: 9pt;")

    def _seleccion(self):
        uid = uid_fila(self.tabla)
        if uid is None:
            return
        p = self.ctx.pacientes.obtener(uid)
        if p is None:
            return
        self.id_sel = p.id_paciente
        self.txt_cedula.setText(p.cedula)
        self.txt_cedula.setEnabled(False)               # la cédula (clave) no se modifica
        self.txt_nombre.setText(p.nombre_completo)
        self.txt_edad.setText(str(p.edad))
        self.cmb_sexo.setCurrentText(p.sexo)
        self.txt_tel.setText(p.telefono)
        self.txt_peso.setText(f"{p.peso_kg:g}")
        self.txt_altura.setText(f"{p.altura_m:g}")

    def _leer(self) -> dict:
        return dict(cedula=self.txt_cedula.text(), nombre_completo=self.txt_nombre.text(),
                    edad=self.txt_edad.text(), sexo=self.cmb_sexo.currentText(),
                    telefono=self.txt_tel.text(), peso_kg=self.txt_peso.text(),
                    altura_m=self.txt_altura.text())

    def limpiar(self):
        self.id_sel = None
        for w in (self.txt_cedula, self.txt_nombre, self.txt_edad, self.txt_tel, self.txt_peso,
                  self.txt_altura):
            w.clear()
        self.txt_cedula.setEnabled(self.editable)
        self.cmb_sexo.setCurrentIndex(0)
        self.tabla.clearSelection()
        self.tabla.setCurrentCell(-1, -1)

    def guardar(self):
        if self.id_sel is not None:
            return aviso(self, "Hay un paciente seleccionado. Pulse «Limpiar formulario» para registrar uno nuevo.")
        try:
            p = self.ctx.pacientes.crear(self._leer())
        except Exception as e:
            return error(self, e)
        exito(self, f"Paciente «{p.nombre_completo}» registrado correctamente.")
        self.limpiar()
        self.cargar_tabla()

    def modificar(self):
        if self.id_sel is None:
            return aviso(self, "Seleccione primero un paciente de la tabla para modificarlo.")
        try:
            self.ctx.pacientes.actualizar(self.id_sel, self._leer())
        except Exception as e:
            return error(self, e)
        exito(self, "Datos del paciente actualizados correctamente.")
        self.limpiar()
        self.cargar_tabla()

    def eliminar(self):
        if self.id_sel is None:
            return aviso(self, "Seleccione el paciente que desea dar de baja.")
        if not confirmar(self, f"¿Desea dar de baja al paciente '{self.txt_cedula.text()}'?"):
            return
        try:
            self.ctx.pacientes.eliminar(self.id_sel)
        except Exception as e:
            return error(self, e)
        exito(self, "Paciente dado de baja.")
        self.limpiar()
        self.cargar_tabla()
