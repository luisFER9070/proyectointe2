# Archivo: vistas/login.py
# RF-01: pantalla de inicio de sesión con acceso diferenciado por rol.
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout, QWidget)

from seed import CREDENCIALES_DEMO
from . import theme as T
from .widgets import Logo, PulsoECG, boton, etiqueta


class LoginVentana(QWidget):
    acceso_concedido = Signal()

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("Sistema Gestor de Consultas y Expedientes de Pacientes · Acceso")
        self.resize(1080, 680)
        self.setMinimumSize(900, 600)
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._panel_marca(), 11)
        raiz.addWidget(self._panel_formulario(), 10)

    # ------------------------------------------------------- panel izquierdo ---
    def _panel_marca(self) -> QWidget:
        p = QFrame()
        p.setObjectName("loginIzq")
        lay = QVBoxLayout(p)
        lay.setContentsMargins(56, 48, 56, 36)
        lay.setSpacing(0)
        fila = QHBoxLayout()
        fila.setSpacing(14)
        fila.addWidget(Logo(60, invertido=True))
        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(etiqueta("UNAN-León", "h3"))
        col.itemAt(0).widget().setStyleSheet("color: #CFEBEE; font-weight: 700; font-size: 11pt;")
        sub = etiqueta("Proyecto Integrador II · Ingeniería en Sistemas")
        sub.setStyleSheet("color: #BFE3E6; font-size: 9pt;")
        col.addWidget(sub)
        fila.addLayout(col)
        fila.addStretch()
        lay.addLayout(fila)
        lay.addStretch(2)
        titulo = QLabel("Cuidar es nuestra\nvocación.")
        titulo.setStyleSheet("font-size: 34pt; font-weight: 800; color: white; line-height: 110%;")
        lay.addWidget(titulo)
        lay.addSpacing(14)
        desc = QLabel("Sistema Gestor de Consultas y Expedientes de Pacientes: "
                      "la historia clínica de cada persona, ordenada, segura y al alcance "
                      "del personal de salud.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11.5pt; color: #E2F4F6;")
        lay.addWidget(desc)
        lay.addSpacing(18)
        for ic, tx in (("", "Acceso seguro por rol y permisos"),
                       ("", "Expedientes con historial de consultas"),
                       ("", "Atención médica trazable y auditada")):
            lb = QLabel(f"{ic}   {tx}")
            lb.setStyleSheet("font-size: 10.5pt; color: white; padding: 3px 0;")
            lay.addWidget(lb)
        lay.addStretch(1)
        lay.addWidget(PulsoECG("#FFFFFF"))
        lay.addSpacing(10)
        pie = QLabel("Grupo GP4 · León, Nicaragua")
        pie.setStyleSheet("color: #BFE3E6; font-size: 9pt;")
        lay.addWidget(pie)
        return p

    # ------------------------------------------------------- panel derecho ----
    def _panel_formulario(self) -> QWidget:
        p = QFrame()
        p.setObjectName("loginDer")
        ext = QVBoxLayout(p)
        ext.setContentsMargins(0, 0, 0, 0)
        ext.addStretch()
        centro = QHBoxLayout()
        centro.addStretch()
        form = QWidget()
        form.setFixedWidth(400)
        lay = QVBoxLayout(form)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(etiqueta("Bienvenido(a)", "h1"))
        lay.addWidget(etiqueta("Seleccione su perfil e ingrese sus credenciales.", "muted"))
        lay.addSpacing(14)

        lay.addWidget(etiqueta("PERFIL DE ACCESO", "campo"))
        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(True)
        for clave, texto in (("admin", "Administrador"), ("doctor", "Médico"),
                             ("enfermera", "Enfermería")):
            b = QPushButton(texto)
            b.setObjectName("rolBtn")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(66)
            b.clicked.connect(lambda _=False, c=clave: self._elegir_perfil(c))
            self.grupo.addButton(b)
            fila.addWidget(b)
        lay.addLayout(fila)
        lay.addSpacing(8)

        lay.addWidget(etiqueta("USUARIO", "campo"))
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Nombre de usuario")
        lay.addWidget(self.txt_usuario)
        lay.addWidget(etiqueta("CONTRASEÑA", "campo"))
        self.txt_clave = QLineEdit()
        self.txt_clave.setEchoMode(QLineEdit.Password)
        self.txt_clave.setPlaceholderText("••••••••")
        lay.addWidget(self.txt_clave)
        chk = QCheckBox("Mostrar contraseña")
        chk.toggled.connect(lambda v: self.txt_clave.setEchoMode(QLineEdit.Normal if v else QLineEdit.Password))
        lay.addWidget(chk)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(f"color: {T.ROJO}; font-weight: 600;")
        self.lbl_error.setWordWrap(True)
        lay.addWidget(self.lbl_error)
        self.btn_ingresar = boton("Ingresar al sistema", "primary", self._ingresar)
        self.btn_ingresar.setMinimumHeight(46)
        self.btn_ingresar.setDefault(True)
        lay.addWidget(self.btn_ingresar)
        lay.addSpacing(10)
        demo = QLabel("Credenciales de demostración\n"
                      "admin / admin123   ·   doctor / doctor123   ·   enfermera / enfermera123")
        demo.setObjectName("aviso")
        demo.setWordWrap(True)
        demo.setStyleSheet("font-size: 9pt;")
        lay.addWidget(demo)
        for campo_ in (self.txt_usuario, self.txt_clave):
            campo_.returnPressed.connect(self._ingresar)
        centro.addWidget(form)
        centro.addStretch()
        ext.addLayout(centro)
        ext.addStretch()
        return p

    # ------------------------------------------------------------- acciones ---
    def _elegir_perfil(self, clave: str):
        usuario, clave_demo = CREDENCIALES_DEMO[clave]
        self.txt_usuario.setText(usuario)
        self.txt_clave.setText(clave_demo)
        self.lbl_error.clear()
        self.btn_ingresar.setFocus()

    def _ingresar(self):
        try:
            self.ctx.auth.iniciar_sesion(self.txt_usuario.text(), self.txt_clave.text())
        except ValueError as e:
            self.lbl_error.setText(f"{e}")
            self.txt_clave.clear()
            self.txt_clave.setFocus()
            return
        self.lbl_error.clear()
        self.acceso_concedido.emit()

    def reiniciar(self):
        self.txt_usuario.clear()
        self.txt_clave.clear()
        self.lbl_error.clear()
        b = self.grupo.checkedButton()
        if b:
            self.grupo.setExclusive(False)
            b.setChecked(False)
            self.grupo.setExclusive(True)
