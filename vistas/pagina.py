# Archivo: vistas/pagina.py
from PySide6.QtWidgets import QWidget


class Pagina(QWidget):
    """Clase base de las pantallas del menú. `refrescar()` recarga datos al mostrarse."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setObjectName("contenido")

    def puede(self, clave: str) -> bool:
        return self.ctx.sesion.puede(clave)

    def refrescar(self):
        pass
