# Archivo: vistas/ventana.py
# Ventana principal: menú lateral según los permisos del rol, usuario en sesión
# y botón para cerrar sesión (Sesión 14 del informe).
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from permisos import ETIQUETA_ROL
from .p_bitacora import PaginaBitacora
from .p_citas import PaginaCitas
from .p_consultas import PaginaConsultas
from .p_expedientes import PaginaExpedientes
from .p_inicio import PaginaInicio
from .p_medicos import PaginaMedicos
from .p_pacientes import PaginaPacientes
from .p_reportes import PaginaReportes
from .p_usuarios import PaginaUsuarios
from .widgets import Logo, boton, chip

# (clave, texto del menú, permiso necesario, clase de página)
MENU = [
    ("inicio", "Inicio", "panel.ver", PaginaInicio),
    ("pacientes", "Pacientes", "pacientes.ver", PaginaPacientes),
    ("expedientes", "Expedientes", "expedientes.ver", PaginaExpedientes),
    ("consultas", "Consultas", "consultas.ver", PaginaConsultas),
    ("citas", "Citas", "citas.ver", PaginaCitas),
    ("medicos", "Médicos", "medicos.gestionar", PaginaMedicos),
    ("usuarios", "Usuarios y permisos", "usuarios.gestionar", PaginaUsuarios),
    ("bitacora", "Bitácora", "bitacora.ver", PaginaBitacora),
    ("reportes", "Reportes", "reportes.generar", PaginaReportes),
]


class VentanaPrincipal(QMainWindow):
    cerrar_sesion = Signal()

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("Sistema Gestor de Consultas y Expedientes de Pacientes")
        self.resize(1360, 820)
        self.setMinimumSize(1200, 760)
        raiz = QWidget()
        self.setCentralWidget(raiz)
        lay = QHBoxLayout(raiz)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.paginas: dict[str, QWidget] = {}
        self.botones: dict[str, QPushButton] = {}
        self.stack = QStackedWidget()
        self.stack.setObjectName("contenido")
        lay.addWidget(self._barra_lateral())
        marco = QWidget()
        marco.setObjectName("contenido")
        m = QVBoxLayout(marco)
        m.setContentsMargins(28, 24, 28, 24)
        m.addWidget(self.stack)
        lay.addWidget(marco, 1)

        for clave, _t, permiso, clase in MENU:
            if self.ctx.sesion.puede(permiso):
                pag = clase(ctx)
                self.paginas[clave] = pag
                self.stack.addWidget(pag)
        # Atajo Expedientes -> Consultas (registrar una consulta del expediente abierto)
        if "expedientes" in self.paginas and "consultas" in self.paginas:
            self.paginas["expedientes"].abrir_consulta.connect(self._abrir_consulta)
        if "inicio" in self.paginas:
            self.paginas["inicio"].ir_a.connect(self.ir_a)
        self.stack.currentChanged.connect(lambda i: self.stack.widget(i).refrescar())
        self.ir_a(next(iter(self.paginas)))

    def _barra_lateral(self) -> QWidget:
        lado = QFrame()
        lado.setObjectName("sidebar")
        lado.setFixedWidth(262)
        lay = QVBoxLayout(lado)
        lay.setContentsMargins(16, 24, 16, 18)
        lay.setSpacing(4)
        marca = QHBoxLayout()
        marca.setSpacing(11)
        marca.addWidget(Logo(46, invertido=True))
        col = QVBoxLayout()
        col.setSpacing(0)
        a = QLabel("Expedientes\nClínicos")
        a.setObjectName("marca")
        b = QLabel("Gestión de consultas")
        b.setObjectName("submarca")
        col.addWidget(a)
        col.addWidget(b)
        marca.addLayout(col)
        marca.addStretch()
        lay.addLayout(marca)
        lay.addSpacing(22)

        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        for clave, texto, permiso, _c in MENU:
            if not self.ctx.sesion.puede(permiso):
                continue
            btn = QPushButton(texto)
            btn.setObjectName("menu")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=clave: self.ir_a(k))
            grupo.addButton(btn)
            self.botones[clave] = btn
            lay.addWidget(btn)
        lay.addStretch()

        u = self.ctx.sesion.usuario
        tarjeta = QFrame()
        tarjeta.setObjectName("usuarioCard")
        t = QVBoxLayout(tarjeta)
        t.setContentsMargins(14, 14, 14, 14)
        t.setSpacing(8)
        fila = QHBoxLayout()
        fila.setSpacing(10)
        av = QLabel(u.nombre_completo.replace("Dra. ", "").replace("Dr. ", "").replace("Enf. ", "")[:1].upper())
        av.setFixedSize(40, 40)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet("background: white; color: #0B4F6C; border-radius: 20px; "
                         "font-weight: 800; font-size: 14pt;")
        fila.addWidget(av)
        info = QVBoxLayout()
        info.setSpacing(2)
        nom = QLabel(u.nombre_completo)
        nom.setWordWrap(True)
        nom.setStyleSheet("font-weight: 700; font-size: 9.5pt; color: white;")
        info.addWidget(nom)
        rol = QLabel(ETIQUETA_ROL.get(u.rol.nombre, u.rol.nombre))
        rol.setStyleSheet("color: #BFE3E6; font-size: 9pt;")
        info.addWidget(rol)
        fila.addLayout(info, 1)
        t.addLayout(fila)
        salir = boton("Cerrar sesión", "default", self._salir)
        salir.setObjectName("salir")
        t.addWidget(salir)
        lay.addWidget(tarjeta)
        return lado

    def ir_a(self, clave: str):
        if clave not in self.paginas:
            return
        self.botones[clave].setChecked(True)
        pag = self.paginas[clave]
        if self.stack.currentWidget() is pag:
            pag.refrescar()
        else:
            self.stack.setCurrentWidget(pag)

    def _abrir_consulta(self, id_expediente: int):
        self.ir_a("consultas")
        self.paginas["consultas"].seleccionar_expediente(id_expediente)

    def _salir(self):
        self.ctx.auth.cerrar_sesion()
        self.cerrar_sesion.emit()
