# Archivo: database.py
# Capa de persistencia: motor, sesión del ORM y creación del esquema.
# Por defecto usa SQLite (archivo local). Para MySQL basta definir la variable
# de entorno DATABASE_URL, por ejemplo:
#   mysql+pymysql://usuario:clave@localhost/sistema_consultas_medicas?charset=utf8mb4
import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models import Base

RUTA_DB = Path(__file__).with_name("sistema_consultas.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{RUTA_DB}")


class Database:
    def __init__(self, url: str | None = None):
        self.engine = create_engine(url or DATABASE_URL, future=True)
        if self.engine.dialect.name == "sqlite":
            @event.listens_for(self.engine, "connect")
            def _activar_fk(conexion, _registro):      # SQLite no aplica FK por defecto
                cur = conexion.cursor()
                cur.execute("PRAGMA foreign_keys=ON")
                cur.close()
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()

    def cerrar(self):
        self.session.close()
        self.engine.dispose()
