#para ejecutar archivo usar 
# cd /d "C:\Users\HP VICTUS\Desktop\sistema_clinico"
# python main.py


# Archivo: main.py
# Capa de Presentación - punto de entrada (Proyecto Integrador II, UNAN-León)
# Sistema Gestor de Consultas y Expedientes de Pacientes
#
# Ejecutar con:   python main.py
# Requiere:       pip install -r requirements.txt
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from controller import Contexto
from database import Database
from seed import sembrar_si_vacia
from vistas import theme
from vistas.login import LoginVentana
from vistas.ventana import VentanaPrincipal


class Aplicacion:
    """Alterna entre la pantalla de acceso y la ventana principal."""

    def __init__(self):
        self.db = Database()
        sembrar_si_vacia(self.db)
        self.ctx = Contexto(self.db)
        self.login = LoginVentana(self.ctx)
        self.login.acceso_concedido.connect(self.abrir_principal)
        self.principal = None

    def iniciar(self):
        self.login.show()

    def abrir_principal(self):
        self.principal = VentanaPrincipal(self.ctx)
        self.principal.cerrar_sesion.connect(self.volver_al_login)
        self.principal.showMaximized()
        self.login.hide()

    def volver_al_login(self):
        if self.principal:
            self.principal.close()
            self.principal.deleteLater()
            self.principal = None
        self.login.reiniciar()
        self.login.show()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(theme.QSS)
    app.setFont(QFont("Segoe UI", 10))
    aplicacion = Aplicacion()
    aplicacion.iniciar()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
