# Archivo: reportes_pdf.py
# RF-11: reportes en PDF con plantilla institucional (pacientes, expediente de un
# paciente y consultas por médico / rango de fechas). Registra EXPORTAR en la bitácora.
from __future__ import annotations

from datetime import date, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select

from controller import _Base
from models import Consulta, Expediente, Paciente

TEAL = colors.HexColor("#0E7C86")
AZUL = colors.HexColor("#0B4F6C")
MENTA = colors.HexColor("#E6F4F5")
GRIS = colors.HexColor("#5B7480")

_est = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_est["Heading1"], textColor=AZUL, fontSize=17, spaceAfter=2)
H2 = ParagraphStyle("h2", parent=_est["Heading2"], textColor=TEAL, fontSize=12, spaceBefore=10, spaceAfter=4)
TXT = ParagraphStyle("txt", parent=_est["BodyText"], fontSize=9, leading=12)
CEL = ParagraphStyle("cel", parent=TXT, fontSize=8, leading=10)
CELH = ParagraphStyle("celh", parent=CEL, textColor=colors.white, fontName="Helvetica-Bold")
MUTED = ParagraphStyle("mut", parent=TXT, textColor=GRIS)


def _tabla(encabezados, filas, anchos=None):
    datos = [[Paragraph(h, CELH) for h in encabezados]]
    datos += [[Paragraph(str(c), CEL) for c in fila] for fila in filas]
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, MENTA]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9DDE0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


class ReporteController(_Base):
    # ---------------------------------------------------------- utilidades ---
    def _pdf(self, ruta, titulo, subtitulo, bloques, horizontal=False):
        tam = landscape(letter) if horizontal else letter
        usuario = self.sesion.usuario.nombre_completo if self.sesion.usuario else "—"

        def decorar(canvas, doc):
            w, h = tam
            canvas.saveState()
            canvas.setFillColor(AZUL)
            canvas.rect(0, h - 1.6 * cm, w, 1.6 * cm, stroke=0, fill=1)
            canvas.setFillColor(TEAL)
            canvas.rect(0, h - 1.75 * cm, w, 0.15 * cm, stroke=0, fill=1)
            canvas.setFillColor(colors.white)           # cruz médica
            canvas.roundRect(1.5 * cm, h - 1.3 * cm, 0.9 * cm, 0.25 * cm, 0.08 * cm, stroke=0, fill=1)
            canvas.roundRect(1.82 * cm, h - 1.62 * cm, 0.25 * cm, 0.9 * cm, 0.08 * cm, stroke=0, fill=1)
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(2.8 * cm, h - 1.05 * cm, "Sistema Gestor de Consultas y Expedientes de Pacientes")
            canvas.setFont("Helvetica", 8)
            canvas.drawString(2.8 * cm, h - 1.4 * cm, "UNAN-León · Proyecto Integrador II")
            canvas.setFillColor(GRIS)
            canvas.setFont("Helvetica", 7.5)
            canvas.drawString(1.5 * cm, 0.9 * cm,
                              f"Generado por {usuario} · {datetime.now():%d/%m/%Y %H:%M} · Documento confidencial")
            canvas.drawRightString(w - 1.5 * cm, 0.9 * cm, f"Página {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(str(ruta), pagesize=tam, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                                topMargin=2.5 * cm, bottomMargin=1.6 * cm, title=titulo)
        cuerpo = [Paragraph(titulo, H1), Paragraph(subtitulo, MUTED), Spacer(1, 8)] + bloques
        doc.build(cuerpo, onFirstPage=decorar, onLaterPages=decorar)

    def _cerrar(self, ruta, referencia):
        self._log("EXPORTAR", "reportes", referencia)
        self._commit()
        return str(ruta)

    # ------------------------------------------------------------- reportes ---
    def pacientes(self, ruta):
        self.sesion.exigir("reportes.generar")
        lista = list(self.s.scalars(select(Paciente).order_by(Paciente.nombre_completo)))
        filas = [(p.cedula, p.nombre_completo, p.edad, p.sexo, p.telefono, f"{p.peso_kg:.1f}",
                  f"{p.altura_m:.2f}", f"{p.calcular_imc():.1f}", p.clasificar_imc(),
                  p.expediente.numero if p.expediente else "—") for p in lista]
        bloques = [_tabla(["Cédula", "Paciente", "Edad", "Sexo", "Teléfono", "Peso (kg)",
                           "Altura (m)", "IMC", "Clasificación", "Expediente"], filas,
                          [3.2 * cm, 6 * cm, 1.2 * cm, 2 * cm, 2.2 * cm, 1.8 * cm, 1.8 * cm,
                           1.2 * cm, 2.4 * cm, 2.2 * cm])]
        self._pdf(ruta, "Listado de pacientes", f"Total de pacientes registrados: {len(lista)}",
                  bloques, horizontal=True)
        return self._cerrar(ruta, f"pacientes ({len(lista)})")

    def expediente(self, ruta, id_expediente: int):
        self.sesion.exigir("reportes.generar")
        e = self.s.get(Expediente, id_expediente)
        if e is None:
            raise ValueError("Seleccione un expediente.")
        p = e.paciente
        ficha = Table([
            [Paragraph("<b>Paciente</b>", TXT), Paragraph(p.nombre_completo, TXT),
             Paragraph("<b>Cédula</b>", TXT), Paragraph(p.cedula, TXT)],
            [Paragraph("<b>Edad / Sexo</b>", TXT), Paragraph(f"{p.edad} años · {p.sexo}", TXT),
             Paragraph("<b>Teléfono</b>", TXT), Paragraph(p.telefono, TXT)],
            [Paragraph("<b>Tipo de sangre</b>", TXT), Paragraph(e.tipo_sangre, TXT),
             Paragraph("<b>IMC</b>", TXT), Paragraph(f"{p.calcular_imc():.1f} ({p.clasificar_imc()})", TXT)],
            [Paragraph("<b>Alergias</b>", TXT), Paragraph(e.alergias, TXT),
             Paragraph("<b>Apertura</b>", TXT), Paragraph(f"{e.fecha_apertura:%d/%m/%Y}", TXT)],
            [Paragraph("<b>Antecedentes</b>", TXT), Paragraph(e.antecedentes, TXT), "", ""],
        ], colWidths=[3 * cm, 6.5 * cm, 2.6 * cm, 5.5 * cm])
        ficha.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, TEAL), ("BACKGROUND", (0, 0), (0, -1), MENTA),
                                   ("BACKGROUND", (2, 0), (2, -2), MENTA), ("SPAN", (1, 4), (3, 4)),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        filas = [(c.fecha.strftime("%d/%m/%Y"), c.codigo, c.medico.nombre_completo, c.motivo,
                  c.diagnostico, c.tratamiento) for c in e.consultas]          # más reciente primero
        bloques = [ficha, Paragraph("Historial de consultas (de la más reciente a la más antigua)", H2),
                   _tabla(["Fecha", "Código", "Médico", "Motivo", "Diagnóstico", "Tratamiento"], filas,
                          [2 * cm, 2 * cm, 3.6 * cm, 3 * cm, 3 * cm, 4 * cm]) if filas
                   else Paragraph("El paciente aún no tiene consultas registradas.", TXT)]
        self._pdf(ruta, f"Expediente clínico {e.numero}", f"Consultas registradas: {len(filas)}", bloques)
        return self._cerrar(ruta, e.numero)

    def consultas(self, ruta, id_medico: int | None = None, desde: date | None = None,
                  hasta: date | None = None):
        self.sesion.exigir("reportes.generar")
        q = select(Consulta)
        if id_medico:
            q = q.where(Consulta.id_medico == id_medico)
        if desde:
            q = q.where(Consulta.fecha >= desde)
        if hasta:
            q = q.where(Consulta.fecha <= hasta)
        lista = list(self.s.scalars(q.order_by(Consulta.fecha.desc(), Consulta.id_consulta.desc())))
        filas = [(c.fecha.strftime("%d/%m/%Y"), c.codigo, c.expediente.paciente.nombre_completo,
                  c.medico.nombre_completo, c.diagnostico, c.tratamiento) for c in lista]
        rango = f"{desde:%d/%m/%Y}" if desde else "inicio"
        rango += f" – {hasta:%d/%m/%Y}" if hasta else " – hoy"
        bloques = [_tabla(["Fecha", "Código", "Paciente", "Médico", "Diagnóstico", "Tratamiento"], filas,
                          [2.2 * cm, 2.2 * cm, 5 * cm, 4.6 * cm, 4.2 * cm, 6 * cm]) if filas
                   else Paragraph("No hay consultas en el rango seleccionado.", TXT)]
        self._pdf(ruta, "Reporte de consultas médicas", f"Periodo: {rango} · Total: {len(lista)}",
                  bloques, horizontal=True)
        return self._cerrar(ruta, f"consultas ({len(lista)})")
