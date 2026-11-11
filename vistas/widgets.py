# Archivo: vistas/widgets.py
# Componentes visuales reutilizables de la capa de presentación.
from __future__ import annotations

import math
from datetime import date, datetime

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QAbstractButton, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                               QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView)

from . import theme as T


# ------------------------------------------------------------------ Logo ------
class Logo(QWidget):
    """Cruz médica sobre un cuadrado redondeado con degradado (marca del sistema)."""

    def __init__(self, tam: int = 52, invertido: bool = False, parent=None):
        super().__init__(parent)
        self.invertido = invertido
        self.setFixedSize(tam, tam)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        caja = QRectF(1, 1, w - 2, w - 2)
        if self.invertido:
            p.setBrush(QColor("white"))
            fondo_cruz = QColor(T.TEAL)
        else:
            g = QLinearGradient(0, 0, w, w)
            g.setColorAt(0, QColor(T.TEAL_CLARO))
            g.setColorAt(1, QColor(T.AZUL))
            p.setBrush(QBrush(g))
            fondo_cruz = QColor("white")
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(caja, w * 0.28, w * 0.28)
        p.setBrush(fondo_cruz)
        largo, grueso = w * 0.54, w * 0.17
        c = w / 2
        p.drawRoundedRect(QRectF(c - largo / 2, c - grueso / 2, largo, grueso), grueso / 3, grueso / 3)
        p.drawRoundedRect(QRectF(c - grueso / 2, c - largo / 2, grueso, largo), grueso / 3, grueso / 3)


# --------------------------------------------------------- Pulso cardíaco -----
class PulsoECG(QWidget):
    """Línea de electrocardiograma animada (identidad hospitalaria)."""
    _PUNTOS = [(0, 0), (.10, 0), (.14, -.12), (.18, 0), (.26, 0), (.29, .10), (.33, -.85),
               (.37, .35), (.41, 0), (.55, 0), (.62, -.22), (.69, 0), (1, 0)]

    def __init__(self, color: str = "#FFFFFF", parent=None):
        super().__init__(parent)
        self._fase = 0.0
        self._color = QColor(color)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._avanzar)
        self._timer.start(33)
        self.setMinimumHeight(70)

    def _avanzar(self):
        self._fase = (self._fase + 0.006) % 1.0
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        periodo = max(w / 2.2, 160)
        g = QLinearGradient(0, 0, w, 0)
        for pos, alfa in ((0, 0), (.2, 230), (.8, 230), (1, 0)):
            c = QColor(self._color)
            c.setAlpha(alfa)
            g.setColorAt(pos, c)
        pen = QPen(QBrush(g), 3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        ruta = QPainterPath()
        x0 = -self._fase * periodo
        primero = True
        k = 0
        while x0 + k * periodo < w + periodo:
            for px, py in self._PUNTOS:
                pt = QPointF(x0 + (k + px) * periodo, h / 2 + py * h * 0.42)
                if primero:
                    ruta.moveTo(pt)
                    primero = False
                else:
                    ruta.lineTo(pt)
            k += 1
        p.drawPath(ruta)


# --------------------------------------------------------------- Tarjeta ------
class Card(QFrame):
    def __init__(self, margen: int = 18, sombra: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        if sombra:
            fx = QGraphicsDropShadowEffect(self)
            fx.setBlurRadius(26)
            fx.setOffset(0, 4)
            fx.setColor(QColor(11, 79, 108, 38))
            self.setGraphicsEffect(fx)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(margen, margen, margen, margen)
        self.lay.setSpacing(10)


class TarjetaDato(Card):
    """Indicador del panel general: icono, valor grande y título."""

    def __init__(self, icono: str, titulo: str, color: str = T.TEAL, parent=None):
        super().__init__(margen=16, parent=parent)
        self.setFixedHeight(92)
        fila = QHBoxLayout()
        fila.setSpacing(14)
        self.lay.addLayout(fila)
        ic = QLabel(icono)
        ic.setAlignment(Qt.AlignCenter)
        ic.setFixedSize(52, 52) if icono else ic.setFixedSize(8, 52)
        ic.setStyleSheet(f"background: {T.suave(color) if icono else color}; border-radius: {15 if icono else 4}px; font-size: 20pt;")
        fila.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(0)
        self.valor = QLabel("0")
        self.valor.setStyleSheet(f"font-size: 22pt; font-weight: 700; color: {color};")
        t = QLabel(titulo)
        t.setObjectName("muted")
        col.addWidget(self.valor)
        col.addWidget(t)
        fila.addLayout(col)
        fila.addStretch()

    def set_valor(self, v):
        self.valor.setText(str(v))


# ------------------------------------------------- Interruptor (toggle) -------
class Interruptor(QAbstractButton):
    """Interruptor deslizante; se usa en la matriz de permisos por rol."""
    cambio = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 26)
        self.toggled.connect(self.cambio.emit)

    def sizeHint(self):
        return QSize(46, 26)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        on, hab = self.isChecked(), self.isEnabled()
        if on:
            col = QColor(T.TEAL if hab else "#9CCBD0")
        else:
            col = QColor("#C5D4D8" if hab else "#E1EAEC")
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawRoundedRect(QRectF(0, 1, 46, 24), 12, 12)
        p.setBrush(QColor("white"))
        x = 24 if on else 3
        p.drawEllipse(QRectF(x, 4, 18, 18))


# ---------------------------------------------------------- Constructores -----
def boton(texto: str, tipo: str = "default", slot=None, tip: str | None = None) -> QPushButton:
    b = QPushButton(texto)
    b.setCursor(Qt.PointingHandCursor)
    if tipo != "default":
        b.setProperty("kind", tipo)
    if slot:
        b.clicked.connect(slot)
    if tip:
        b.setToolTip(tip)
    return b


def etiqueta(texto: str, nombre: str = "") -> QLabel:
    lb = QLabel(texto)
    if nombre:
        lb.setObjectName(nombre)
    return lb


def encabezado_pagina(titulo: str, subtitulo: str, icono: str = "") -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 4)
    lay.setSpacing(2)
    lay.addWidget(etiqueta(f"{icono}  {titulo}" if icono else titulo, "h1"))
    lay.addWidget(etiqueta(subtitulo, "muted"))
    return w


def chip(texto: str, fondo: str = T.MENTA, color: str = T.AZUL) -> QLabel:
    lb = QLabel(texto)
    lb.setAlignment(Qt.AlignCenter)
    lb.setStyleSheet(f"background: {fondo}; color: {color}; border-radius: 11px; "
                     f"padding: 3px 12px; font-weight: 700; font-size: 9pt;")
    return lb


def campo(texto: str) -> QLabel:
    return etiqueta(texto.upper(), "campo")


def crear_tabla(encabezados: list[str], expandir: int | None = None) -> QTableWidget:
    t = QTableWidget(0, len(encabezados))
    t.setHorizontalHeaderLabels(encabezados)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.setWordWrap(False)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(40)
    t.setFocusPolicy(Qt.NoFocus)
    h = t.horizontalHeader()
    h.setHighlightSections(False)
    h.setMinimumSectionSize(48)
    if expandir is None:
        h.setSectionResizeMode(QHeaderView.Stretch)
    else:
        h.setSectionResizeMode(QHeaderView.ResizeToContents)
        h.setSectionResizeMode(expandir, QHeaderView.Stretch)
    return t


def celda(texto, centro: bool = False, color: str | None = None, negrita: bool = False,
          uid=None, fondo: str | None = None) -> QTableWidgetItem:
    it = QTableWidgetItem(str(texto))
    if centro:
        it.setTextAlignment(Qt.AlignCenter)
    if color:
        it.setForeground(QColor(color))
    if negrita:
        f = QFont(it.font())
        f.setBold(True)
        it.setFont(f)
    if fondo:
        it.setBackground(QColor(fondo))
    if uid is not None:
        it.setData(Qt.UserRole, uid)
    it.setToolTip(str(texto))
    return it


def uid_fila(tabla: QTableWidget):
    """Identificador (Qt.UserRole de la columna 0) de la fila seleccionada."""
    fila = tabla.currentRow()
    if fila < 0 or tabla.item(fila, 0) is None:
        return None
    return tabla.item(fila, 0).data(Qt.UserRole)


def seleccionar_uid(tabla: QTableWidget, uid) -> bool:
    for fila in range(tabla.rowCount()):
        if tabla.item(fila, 0) and tabla.item(fila, 0).data(Qt.UserRole) == uid:
            tabla.selectRow(fila)
            return True
    return False


def color_imc(clasificacion: str) -> str:
    return {"Bajo peso": T.AMBAR, "Normal": T.VERDE, "Sobrepeso": T.AMBAR,
            "Obesidad": T.ROJO}.get(clasificacion, T.TEXTO)


def fecha_txt(f) -> str:
    if isinstance(f, datetime):
        return f.strftime("%d/%m/%Y %H:%M")
    if isinstance(f, date):
        return f.strftime("%d/%m/%Y")
    return "—"


# -------------------------------------------------------------- Mensajes ------
def aviso(parent, texto: str):
    QMessageBox.warning(parent, "Aviso", texto)


def exito(parent, texto: str):
    QMessageBox.information(parent, "Listo", texto)


def error(parent, exc: Exception):
    titulo = "Acceso denegado" if isinstance(exc, PermissionError) else "No se pudo completar"
    QMessageBox.critical(parent, titulo, str(exc))


def confirmar(parent, texto: str) -> bool:
    r = QMessageBox.question(parent, "Confirmación", texto,
                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return r == QMessageBox.Yes
