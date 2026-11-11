# Archivo: vistas/theme.py
# Identidad visual hospitalaria: verde-azulado clínico, blancos limpios y acentos
# suaves. Un solo lugar para colores y la hoja de estilos (QSS) de toda la aplicación.
AZUL = "#0B4F6C"        # azul hospital (profundo)
TEAL = "#0E7C86"        # verde-azulado principal
TEAL_CLARO = "#13A3AE"
MENTA = "#E6F4F5"       # fondo de realces
FONDO = "#F1F7F9"
TARJETA = "#FFFFFF"
TEXTO = "#12343B"
MUTED = "#5B7480"
BORDE = "#D5E5E8"
ROJO = "#D64545"        # sangre / alertas
AMBAR = "#E9A23B"
VERDE = "#2E9E6B"
FUENTE = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"

QSS = f"""
* {{ font-family: {FUENTE}; font-size: 10.5pt; color: {TEXTO}; }}
QMainWindow, QDialog, #contenido {{ background: {FONDO}; }}
QToolTip {{ background: {AZUL}; color: white; border: none; padding: 5px 8px; }}

/* ---------- Tarjetas y textos ---------- */
#card {{ background: {TARJETA}; border: 1px solid {BORDE}; border-radius: 14px; }}
QLabel {{ background: transparent; }}
QLabel#h1 {{ font-size: 21pt; font-weight: 700; color: {AZUL}; }}
QLabel#h2 {{ font-size: 13pt; font-weight: 700; color: {AZUL}; }}
QLabel#h3 {{ font-size: 10.5pt; font-weight: 600; color: {TEAL}; }}
QLabel#muted {{ color: {MUTED}; font-size: 9.5pt; }}
QLabel#campo {{ color: {MUTED}; font-size: 9pt; font-weight: 600; }}
QLabel#aviso {{ background: {MENTA}; color: {AZUL}; border: 1px solid {BORDE};
               border-radius: 10px; padding: 8px 12px; }}

/* ---------- Campos de entrada ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QDateTimeEdit, QSpinBox {{
    background: white; border: 1.5px solid {BORDE}; border-radius: 9px;
    padding: 7px 10px; selection-background-color: {TEAL}; selection-color: white; }}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus {{
    border: 1.5px solid {TEAL}; }}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QDateEdit:disabled,
QDateTimeEdit:disabled {{ background: #EEF3F5; color: {MUTED}; }}
QLineEdit[readOnly="true"] {{ background: #EEF5F6; color: {AZUL}; font-weight: 600; }}
QComboBox::drop-down, QDateEdit::drop-down, QDateTimeEdit::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: white; border: 1px solid {BORDE};
    selection-background-color: {MENTA}; selection-color: {AZUL}; outline: none; padding: 4px; }}

/* ---------- Botones ---------- */
QPushButton {{ border: none; border-radius: 10px; padding: 9px 14px; font-weight: 600;
               background: {MENTA}; color: {AZUL}; }}
QPushButton:hover {{ background: #D2ECEE; }}
QPushButton:pressed {{ background: #BFE3E6; }}
QPushButton:disabled {{ background: #E9EFF1; color: #9DB0B7; }}
QPushButton[kind="primary"] {{ background: {TEAL}; color: white; }}
QPushButton[kind="primary"]:hover {{ background: {TEAL_CLARO}; }}
QPushButton[kind="primary"]:pressed {{ background: {AZUL}; }}
QPushButton[kind="warn"] {{ background: {AMBAR}; color: white; }}
QPushButton[kind="warn"]:hover {{ background: #F0B258; }}
QPushButton[kind="danger"] {{ background: {ROJO}; color: white; }}
QPushButton[kind="danger"]:hover {{ background: #E26161; }}
QPushButton[kind="ghost"] {{ background: transparent; color: {MUTED}; border: 1.5px solid {BORDE}; }}
QPushButton[kind="ghost"]:hover {{ background: {MENTA}; color: {AZUL}; }}
QPushButton[kind="primary"]:disabled, QPushButton[kind="warn"]:disabled,
QPushButton[kind="danger"]:disabled {{ background: #E9EFF1; color: #9DB0B7; }}

/* ---------- Tablas ---------- */
QTableWidget {{ background: white; alternate-background-color: #F6FAFB; border: 1px solid {BORDE};
    border-radius: 10px; gridline-color: transparent; selection-background-color: {MENTA};
    selection-color: {AZUL}; outline: none; }}
QTableWidget::item {{ padding: 6px 8px; border-bottom: 1px solid #EDF3F5; }}
QTableWidget::item:selected {{ background: #D7EEF0; color: {AZUL}; }}
QHeaderView::section {{ background: {AZUL}; color: white; font-weight: 600; font-size: 9.5pt;
    padding: 9px 6px; border: none; }}
QHeaderView::section:first {{ border-top-left-radius: 9px; }}
QHeaderView::section:last {{ border-top-right-radius: 9px; }}
QTableCornerButton::section {{ background: {AZUL}; border: none; }}

/* ---------- Pestañas ---------- */
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 10px 22px; margin-right: 6px;
    font-weight: 600; border-bottom: 3px solid transparent; }}
QTabBar::tab:selected {{ color: {TEAL}; border-bottom: 3px solid {TEAL}; }}
QTabBar::tab:hover:!selected {{ color: {AZUL}; }}

/* ---------- Varios ---------- */
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 6px; border: 1.5px solid #9DB8BE;
    background: white; }}
QCheckBox::indicator:checked {{ background: {TEAL}; border-color: {TEAL}; }}
QCheckBox::indicator:disabled {{ background: #E3ECEE; border-color: #CBDADD; }}
QCheckBox::indicator:checked:disabled {{ background: #8CC3C8; border-color: #8CC3C8; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #BBD3D7; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {TEAL}; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #BBD3D7; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QSplitter::handle {{ background: transparent; }}
QTextBrowser {{ background: white; border: 1.5px solid {BORDE}; border-radius: 9px; padding: 8px; }}
QProgressBar {{ background: #E4EEF0; border: none; border-radius: 5px; height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {TEAL}, stop:1 {TEAL_CLARO});
    border-radius: 5px; }}
QMessageBox {{ background: white; }}

/* ---------- Barra lateral ---------- */
#sidebar {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {AZUL}, stop:1 {TEAL}); }}
#sidebar QLabel {{ color: white; }}
#sidebar QLabel#marca {{ font-size: 12.5pt; font-weight: 700; }}
#sidebar QLabel#submarca {{ font-size: 8.5pt; color: #BFE3E6; }}
QPushButton#menu {{ background: transparent; color: #DDF1F3; text-align: left; padding: 11px 16px;
    border-radius: 11px; font-weight: 500; }}
QPushButton#menu:hover {{ background: rgba(255,255,255,0.13); color: white; }}
QPushButton#menu:checked {{ background: white; color: {AZUL}; font-weight: 700; }}
QFrame#usuarioCard {{ background: rgba(255,255,255,0.14); border-radius: 13px; }}
QPushButton#salir {{ background: rgba(255,255,255,0.18); color: white; }}
QPushButton#salir:hover {{ background: {ROJO}; }}

/* ---------- Inicio de sesión ---------- */
#loginIzq {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {AZUL}, stop:1 {TEAL_CLARO}); }}
#loginIzq QLabel {{ color: white; }}
#loginDer {{ background: white; }}
QPushButton#rolBtn {{ background: white; border: 1.5px solid {BORDE}; border-radius: 12px;
    padding: 10px 6px; color: {AZUL}; font-weight: 600; font-size: 9.5pt; }}
QPushButton#rolBtn:hover {{ border-color: {TEAL}; background: {MENTA}; }}
QPushButton#rolBtn:checked {{ border: 2px solid {TEAL}; background: {MENTA}; }}
"""


def suave(color: str, alfa: float = 0.14) -> str:
    """Convierte '#RRGGBB' en un rgba() transparente para fondos suaves."""
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    return f"rgba({r},{g},{b},{alfa})"
