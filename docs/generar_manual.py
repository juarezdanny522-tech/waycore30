#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el manual en PDF de WayCore + WayHat (Karbys).

Uso:
    python3 docs/generar_manual.py

Salida:
    docs/Manual_WayCore_WayHat.pdf

Todo el contenido se deriva del código del propio repositorio:
  - WayHat_v6_WayCore.ino                     (firmware ESP32 / pines / protocolo)
  - app/src/main/java/.../MainActivity.kt     (interfaz y permisos)
  - app/src/main/java/.../WayHatService.kt    (enlace Bluetooth SPP)
  - app/src/main/java/.../KarbysService.kt    (voz, TTS, recordatorios)
  - app/src/main/java/.../GeminiClient.kt     (modelo, endpoint, herramientas)
  - app/src/main/AndroidManifest.xml          (permisos y servicios)
  - app/build.gradle.kts                      (SDKs y versión)
"""

import os
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.graphics.shapes import Drawing, Rect, Line, PolyLine, Polygon
from reportlab.graphics.shapes import String as _RLString
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, NextPageTemplate, KeepTogether, ListFlowable, ListItem,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ----------------------------------------------------------------------------
# Paleta y constantes
# ----------------------------------------------------------------------------
AZUL = colors.HexColor("#0B2E4F")
AZUL_CLARO = colors.HexColor("#1D4E79")
TEAL = colors.HexColor("#0E8C86")
TEAL_SUAVE = colors.HexColor("#E4F2F1")
GRIS = colors.HexColor("#5A6672")
GRIS_CLARO = colors.HexColor("#EDF1F5")
GRIS_BORDE = colors.HexColor("#C6D2DC")
NARANJA = colors.HexColor("#B3541E")
AMARILLO_SUAVE = colors.HexColor("#FDF3E3")
ROJO_SUAVE = colors.HexColor("#FBE9E7")
VERDE_SUAVE = colors.HexColor("#E8F5E9")

PAGE_W, PAGE_H = A4
M_LEFT = 2.0 * cm
M_RIGHT = 2.0 * cm
M_TOP = 2.4 * cm
M_BOTTOM = 2.0 * cm
FRAME_W = PAGE_W - M_LEFT - M_RIGHT
FRAME_H = PAGE_H - M_TOP - M_BOTTOM

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(OUT_DIR, "Manual_WayCore_WayHat.pdf")

# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
_ss = getSampleStyleSheet()


def _style(name, **kw):
    base = kw.pop("parent", _ss["BodyText"])
    return ParagraphStyle(name, parent=base, **kw)


S = {
    "body": _style("cuerpo", fontName="Helvetica", fontSize=9.5, leading=13.5,
                   alignment=TA_JUSTIFY, spaceAfter=6, textColor=colors.HexColor("#1A2530")),
    "body_left": _style("cuerpoI", fontName="Helvetica", fontSize=9.5, leading=13.5,
                        alignment=TA_LEFT, spaceAfter=4, textColor=colors.HexColor("#1A2530")),
    "h1": _style("H1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=AZUL,
                 spaceBefore=4, spaceAfter=10),
    "h1x": _style("H1X", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=AZUL,
                  spaceBefore=4, spaceAfter=10),
    "h2": _style("H2", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=AZUL_CLARO,
                 spaceBefore=12, spaceAfter=6),
    "h3": _style("H3", fontName="Helvetica-Bold", fontSize=10.2, leading=13, textColor=TEAL,
                 spaceBefore=9, spaceAfter=4),
    "code": _style("codigo", fontName="Courier", fontSize=7.8, leading=10.2, textColor=colors.HexColor("#12232E"),
                   backColor=GRIS_CLARO, borderPadding=5, leftIndent=3, rightIndent=3,
                   spaceBefore=3, spaceAfter=7, alignment=TA_LEFT),
    "cell": _style("celda", fontName="Helvetica", fontSize=8.2, leading=10.6, alignment=TA_LEFT,
                   textColor=colors.HexColor("#1A2530")),
    "cellb": _style("celdaB", fontName="Helvetica-Bold", fontSize=8.2, leading=10.6, alignment=TA_LEFT,
                    textColor=colors.HexColor("#1A2530")),
    "cellh": _style("celdaH", fontName="Helvetica-Bold", fontSize=8.4, leading=11, alignment=TA_LEFT,
                    textColor=colors.white),
    "cellc": _style("celdaC", fontName="Courier", fontSize=7.6, leading=10, alignment=TA_LEFT,
                    textColor=colors.HexColor("#12232E")),
    "cellcb": _style("celdaCB", fontName="Courier-Bold", fontSize=7.8, leading=10, alignment=TA_LEFT,
                     textColor=colors.HexColor("#12232E")),
    "note": _style("nota", fontName="Helvetica", fontSize=8.8, leading=12, alignment=TA_JUSTIFY,
                   textColor=colors.HexColor("#5A3A12")),
    "bullet": _style("bala", fontName="Helvetica", fontSize=9.3, leading=12.8, alignment=TA_LEFT,
                     textColor=colors.HexColor("#1A2530")),
    "caption": _style("pie", fontName="Helvetica-Oblique", fontSize=8, leading=10.5,
                      alignment=TA_CENTER, textColor=GRIS, spaceBefore=3, spaceAfter=10),
    "toc0": _style("toc0", fontName="Helvetica-Bold", fontSize=9.6, leading=15, textColor=AZUL),
    "toc1": _style("toc1", fontName="Helvetica", fontSize=9, leading=13, leftIndent=16, textColor=GRIS),
    "cover_t": _style("cubT", fontName="Helvetica-Bold", fontSize=27, leading=32, textColor=colors.white,
                      alignment=TA_LEFT),
    "cover_s": _style("cubS", fontName="Helvetica", fontSize=13.5, leading=18, textColor=colors.HexColor("#BBD9E6"),
                      alignment=TA_LEFT),
    "cover_b": _style("cubB", fontName="Helvetica", fontSize=10, leading=14, textColor=GRIS,
                      alignment=TA_LEFT),
}


# ----------------------------------------------------------------------------
# Utilidades de texto
# ----------------------------------------------------------------------------
# Caracteres que las fuentes Type1 estándar (Helvetica/Courier, WinAnsi) no pueden dibujar.
# Se sustituyen por equivalentes ASCII para que el PDF sea idéntico en cualquier equipo.
_SUSTITUCIONES = {
    "\u2192": "->",     # →
    "\u2190": "<-",     # ←
    "\u21c4": "<->",    # ⇄
    "\u03a9": "ohm",    # Ω
    "\u2265": ">=",
    "\u2264": "<=",
    "\u2194": "<->",
}


def _plain(t):
    for k, v in _SUSTITUCIONES.items():
        t = t.replace(k, v)
    return t


def E(t):
    """Escapa texto para Paragraph (permite acentos, bloquea < > &)."""
    return _plain(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(texto, estilo="body"):
    return Paragraph(E(texto), S[estilo])


def PM(texto, estilo="body"):
    """Paragraph con marcado ya escrito a mano."""
    return Paragraph(texto, S[estilo])


def code(texto):
    lineas = [E(l) for l in texto.strip("\n").split("\n")]
    return Paragraph("<br/>".join(lineas).replace(" ", "&nbsp;"), S["code"])


def bullets(items, estilo="bullet"):
    return ListFlowable(
        [ListItem(Paragraph(E(i), S[estilo]), leftIndent=14, value="bulletchar") for i in items],
        bulletType="bullet", start="•", bulletFontSize=8, bulletOffsetY=1,
        leftIndent=12, spaceBefore=2, spaceAfter=6,
    )


def c(texto, estilo="cell"):
    return Paragraph(E(str(texto)), S[estilo])


def cm_(texto, estilo="cellc"):
    txt = E(str(texto)).replace(" ", "&nbsp;").replace("\n", "<br/>")
    return Paragraph(txt, S[estilo])


def tabla(encabezado, filas, anchos, alineaciones=None, tono="azul"):
    """Tabla con encabezado coloreado y filas alternadas."""
    head_bg = AZUL if tono == "azul" else TEAL
    data = [[Paragraph(E(h), S["cellh"]) for h in encabezado]]
    for f in filas:
        data.append(f if isinstance(f, list) else [f])
    t = Table(data, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), head_bg),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    t.setStyle(TableStyle(style))
    return t


def nota(texto, tono="aviso"):
    fondo = AMARILLO_SUAVE if tono == "aviso" else (VERDE_SUAVE if tono == "ok" else ROJO_SUAVE)
    borde = NARANJA if tono == "aviso" else (TEAL if tono == "ok" else colors.HexColor("#C0392B"))
    t = Table([[Paragraph(E(texto), S["note"])]], colWidths=[FRAME_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fondo),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, borde),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def String(x, y, text, **kw):
    """Envoltorio de String que sanea caracteres no soportados por Helvetica."""
    return _RLString(x, y, _plain(text), **kw)


def h1(t):
    return Paragraph(E(t), S["h1"])


def h2(t):
    return Paragraph(E(t), S["h2"])


def h3(t):
    return Paragraph(E(t), S["h3"])


def gap(h=6):
    return Spacer(1, h)


# ----------------------------------------------------------------------------
# Figuras
# ----------------------------------------------------------------------------
def fig_arquitectura():
    d = Drawing(470, 214)
    W, H = 470, 214

    def caja(x, y, w, h, relleno, borde, titulo, sub=None, tc=colors.white, fs=8, ss=6.4):
        d.add(Rect(x, y, w, h, fillColor=relleno, strokeColor=borde, strokeWidth=0.8))
        ty = y + h / 2 + (4 if sub else 0)
        d.add(String(x + w / 2, ty, titulo, fontName="Helvetica-Bold", fontSize=fs,
                     fillColor=tc, textAnchor="middle"))
        if sub:
            d.add(String(x + w / 2, y + h / 2 - 7, sub, fontName="Helvetica", fontSize=ss,
                         fillColor=tc, textAnchor="middle"))

    def flecha(x1, y1, x2, y2, colorb=TEAL, puntos=()):
        d.add(PolyLine([x1, y1] + list(puntos) + [x2, y2], strokeColor=colorb, strokeWidth=1.1))
        # punta horizontal o vertical según el último tramo
        if puntos:
            px, py = puntos[-2], puntos[-1]
        else:
            px, py = x1, y1
        if abs(x2 - px) >= abs(y2 - py):
            s = 1 if x2 >= px else -1
            d.add(Polygon([x2, y2, x2 - 5 * s, y2 + 3, x2 - 5 * s, y2 - 3],
                          fillColor=colorb, strokeColor=colorb))
        else:
            s = 1 if y2 >= py else -1
            d.add(Polygon([x2, y2, x2 - 3, y2 - 5 * s, x2 + 3, y2 - 5 * s],
                          fillColor=colorb, strokeColor=colorb))

    # Caja contenedora del teléfono
    d.add(Rect(272, 74, 198, 122, fillColor=colors.HexColor("#F7FAFC"),
               strokeColor=AZUL, strokeWidth=1.0, strokeDashArray=[3, 2]))
    d.add(String(371, 187, "WayCore  ·  app Android", fontName="Helvetica-Bold",
                 fontSize=8.6, fillColor=AZUL, textAnchor="middle"))

    caja(0, 128, 96, 40, colors.white, GRIS, "Sensores", "3x HC-SR04 · TF-Luna", tc=GRIS)
    d.add(String(48, 136, "DHT11", fontName="Helvetica", fontSize=6.4, fillColor=GRIS, textAnchor="middle"))
    caja(124, 128, 112, 40, AZUL, AZUL, "WayHat", "ESP32-WROOM-32", tc=colors.white)
    caja(283, 133, 176, 32, TEAL, TEAL, "KarbysService", "voz · TTS · recordatorios", fs=8, ss=6.2)
    caja(283, 85, 176, 32, AZUL_CLARO, AZUL_CLARO, "WayHatService", "enlace Bluetooth SPP", fs=8, ss=6.2)
    caja(283, 8, 176, 40, colors.white, TEAL, "Gemini API", "gemini-3.1-flash-lite", tc=TEAL)

    # Sensores -> ESP32
    flecha(96, 148, 124, 148, GRIS)
    d.add(String(110, 152, "GPIO", fontName="Helvetica", fontSize=5.8, fillColor=GRIS, textAnchor="middle"))
    # ESP32 <-> WayHatService (Bluetooth SPP, bidireccional)
    flecha(236, 148, 283, 101, TEAL, puntos=[260, 148, 260, 101])
    d.add(String(262, 130, "Bluetooth", fontName="Helvetica", fontSize=5.8, fillColor=TEAL))
    d.add(String(262, 123, "SPP", fontName="Helvetica", fontSize=5.8, fillColor=TEAL))
    flecha(283, 112, 236, 159, AZUL_CLARO, puntos=[268, 112, 268, 159])
    # Karbys -> Gemini
    flecha(330, 133, 330, 48, TEAL)
    d.add(String(336, 118, "HTTPS / JSON", fontName="Helvetica", fontSize=5.8, fillColor=TEAL))
    d.add(String(336, 111, "x-goog-api-key", fontName="Helvetica", fontSize=5.8, fillColor=TEAL))
    flecha(360, 48, 360, 133, colors.HexColor("#8FB8B4"))
    # Karbys -> WayHat (function calling)
    flecha(300, 133, 300, 117, AZUL_CLARO)
    d.add(String(306, 123, "Function Calling", fontName="Helvetica", fontSize=5.6, fillColor=AZUL_CLARO))
    # Buzzer / vibración
    d.add(String(48, 118, "buzzer  +  vibración", fontName="Helvetica-Oblique", fontSize=5.8,
                 fillColor=NARANJA, textAnchor="middle"))
    d.add(String(48, 111, "avisos de proximidad", fontName="Helvetica-Oblique", fontSize=5.8,
                 fillColor=NARANJA, textAnchor="middle"))
    d.add(String(371, 62, "Internet", fontName="Helvetica-Oblique", fontSize=6, fillColor=GRIS,
                 textAnchor="middle"))
    return d


def fig_cableado():
    d = Drawing(470, 208)

    def caja(x, y, w, h, relleno, borde, lineas, tc=colors.HexColor("#1A2530"),
             bold_first=True, fs=7.2):
        d.add(Rect(x, y, w, h, fillColor=relleno, strokeColor=borde, strokeWidth=0.8))
        total = len(lineas)
        for i, ln in enumerate(lineas):
            yy = y + h - 9 - i * (h - 6) / max(total, 1)
            d.add(String(x + 5, yy, ln, fontName="Helvetica-Bold" if (i == 0 and bold_first) else "Helvetica",
                         fontSize=fs, fillColor=tc))

    # ESP32 central
    d.add(Rect(152, 30, 156, 152, fillColor=colors.HexColor("#F2F7FA"),
               strokeColor=AZUL, strokeWidth=1.1))
    d.add(String(230, 168, "ESP32-WROOM-32", fontName="Helvetica-Bold", fontSize=9,
                 fillColor=AZUL, textAnchor="middle"))
    d.add(String(230, 158, "WayHat  ·  BT \"WayHat-Karbys\"", fontName="Helvetica", fontSize=6.2,
                 fillColor=GRIS, textAnchor="middle"))
    izq = ["GPIO 25  TRIG der.", "GPIO 13  ECHO der.", "GPIO 26  TRIG izq.",
           "GPIO 14  ECHO izq.", "GPIO 27  TRIG tras.", "GPIO 32  ECHO tras.",
           "GPIO 16  RX  <- TF TX", "GPIO 17  TX  -> TF RX", "GPIO 33  DHT11 DATA"]
    for i, t in enumerate(izq):
        d.add(String(158, 143 - i * 12, t, fontName="Courier-Bold", fontSize=6.6, fillColor=colors.HexColor("#12232E")))
    d.add(String(302, 143, "GPIO 4", fontName="Courier-Bold", fontSize=6.6, fillColor=colors.HexColor("#12232E")))
    d.add(String(302, 133, "BUZZER +", fontName="Courier-Bold", fontSize=6.6, fillColor=colors.HexColor("#12232E")))
    d.add(String(230, 112, "Alimentación", fontName="Helvetica-Bold", fontSize=6.8, fillColor=NARANJA,
                 textAnchor="middle"))
    d.add(String(230, 103, "5 V (VIN) y GND", fontName="Helvetica", fontSize=6.4, fillColor=NARANJA,
                 textAnchor="middle"))
    d.add(String(230, 94, "comunes a todos", fontName="Helvetica", fontSize=6.4, fillColor=NARANJA,
                 textAnchor="middle"))
    d.add(String(230, 44, "Serial debug 115200", fontName="Helvetica-Oblique", fontSize=6.2,
                 fillColor=GRIS, textAnchor="middle"))

    # Sensores izquierda
    caja(0, 150, 128, 30, colors.white, GRIS_BORDE, ["HC-SR04 DERECHO", "TRIG 25 · ECHO 13"])
    caja(0, 114, 128, 30, colors.white, GRIS_BORDE, ["HC-SR04 IZQUIERDO", "TRIG 26 · ECHO 14"])
    caja(0, 78, 128, 30, colors.white, GRIS_BORDE, ["HC-SR04 TRASERO", "TRIG 27 · ECHO 32"])
    caja(0, 44, 128, 28, colors.white, GRIS_BORDE, ["TF-Luna (LiDAR)", "TX->16 · RX<-17 · 115200"])
    caja(0, 10, 128, 28, colors.white, GRIS_BORDE, ["DHT11", "DATA -> 33"])

    # Buzzer derecha
    caja(342, 114, 128, 30, colors.white, GRIS_BORDE, ["BUZZER", "+ -> GPIO 4 · - -> GND"])

    # Cables
    for y in (165, 129, 93, 152):
        pass
    cables = [(165, 143), (129, 131), (93, 119), (58, 107), (24, 95)]
    for ys, ye in cables:
        d.add(Line(128, ys, 152, ye, strokeColor=TEAL, strokeWidth=0.9))
    d.add(Line(308, 129, 342, 129, strokeColor=TEAL, strokeWidth=0.9))
    return d


def fig_flujo_voz():
    d = Drawing(470, 60)
    pasos = [("1. Voz / hotword", "\"Oye Karbys\""), ("2. Reconocimiento", "SpeechRecognizer es-MX"),
             ("3. ¿Comando local?", "batería, hora..."), ("4. Gemini + contexto", "Function Calling"),
             ("5. TTS", "Karbys responde")]
    x = 0
    for i, (t, s) in enumerate(pasos):
        d.add(Rect(x, 12, 88, 34, fillColor=(TEAL_SUAVE if i % 2 == 0 else colors.white),
                   strokeColor=TEAL, strokeWidth=0.8))
        d.add(String(x + 44, 36, t, fontName="Helvetica-Bold", fontSize=6.6,
                     fillColor=AZUL, textAnchor="middle"))
        d.add(String(x + 44, 27, s, fontName="Helvetica", fontSize=5.8,
                     fillColor=GRIS, textAnchor="middle"))
        if i < len(pasos) - 1:
            d.add(Line(x + 88, 29, x + 94, 29, strokeColor=TEAL, strokeWidth=1.0))
            d.add(Polygon([x + 98, 29, x + 92, 32, x + 92, 26], fillColor=TEAL, strokeColor=TEAL))
        x += 96
    return d


# ----------------------------------------------------------------------------
# Plantilla de documento con portada y TOC
# ----------------------------------------------------------------------------
class ManualDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            nombre = flowable.style.name
            texto = flowable.getPlainText()
            if nombre == "H1":
                self.notify("TOCEntry", (0, texto, self.page))
            elif nombre == "H2":
                self.notify("TOCEntry", (1, texto, self.page))


def fondo_portada(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AZUL)
    canvas.rect(0, PAGE_H - 11.5 * cm, PAGE_W, 11.5 * cm, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE_H - 12.1 * cm, PAGE_W, 0.6 * cm, stroke=0, fill=1)
    canvas.setFillColor(GRIS_CLARO)
    canvas.rect(0, 0, PAGE_W, 1.6 * cm, stroke=0, fill=1)
    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(M_LEFT, 0.62 * cm, "Documento generado a partir del repositorio waycore30 · Uso interno del equipo WayCorp")
    canvas.restoreState()


def fondo_normal(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(GRIS_CLARO)
    canvas.rect(0, PAGE_H - 1.5 * cm, PAGE_W, 1.5 * cm, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE_H - 1.62 * cm, PAGE_W, 0.12 * cm, stroke=0, fill=1)
    canvas.setFillColor(AZUL)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(M_LEFT, PAGE_H - 1.0 * cm, "WayCore + WayHat · Manual de uso, instalación y conexiones")
    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(PAGE_W - M_RIGHT, PAGE_H - 1.0 * cm, "Karbys · v0.3.0 (firmware v6)")
    canvas.setStrokeColor(GRIS_BORDE)
    canvas.setLineWidth(0.4)
    canvas.line(M_LEFT, 1.35 * cm, PAGE_W - M_RIGHT, 1.35 * cm)
    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(M_LEFT, 0.95 * cm, "WayCorp · Danny Joel Castro Juárez y equipo")
    canvas.drawRightString(PAGE_W - M_RIGHT, 0.95 * cm, "Página %d" % canvas.getPageNumber())
    canvas.restoreState()


# ----------------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------------
def construir_story():
    s = []
    A = s.append

    # ---------------- PORTADA ----------------
    A(Spacer(1, 2.6 * cm))
    A(Paragraph("WayCore + WayHat", S["cover_t"]))
    A(Spacer(1, 0.25 * cm))
    A(Paragraph("Manual de uso, instalación y conexiones", S["cover_s"]))
    A(Spacer(1, 0.5 * cm))
    A(Paragraph("Asistente Karbys · ESP32 · Bluetooth SPP · Gemini", S["cover_s"]))
    A(Spacer(1, 3.4 * cm))

    ficha = [
        [c("Proyecto", "cellb"), c("WayCore — cerebro digital; WayHat — dispositivo físico de apoyo")],
        [c("Asistente", "cellb"), c("Karbys (se pronuncia «guaycor» / Karbys, «guayjat» para WayHat)")],
        [c("App Android", "cellb"), c("com.wayhat.waycore · versionCode 6 · versionName 0.3.0")],
        [c("Firmware", "cellb"), c("WayHat_v6_WayCore.ino · ESP32-WROOM-32 · Bluetooth Classic")],
        [c("Enlaces", "cellb"), c("Bluetooth SPP (teléfono ⇄ WayHat) e Internet HTTPS (teléfono ⇄ Gemini)")],
        [c("Fecha", "cellb"), c("5 de octubre de 2026")],
    ]
    t = Table(ficha, colWidths=[3.6 * cm, FRAME_W - 3.6 * cm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, GRIS_BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]))
    A(t)
    A(Spacer(1, 1.2 * cm))
    A(Paragraph(
        "Este documento explica cómo conectar el hardware, cómo dejar la app lista para funcionar "
        "y cómo utilizarla en el día a día. Todo lo descrito aquí corresponde al código del "
        "repositorio <b>waycore30</b>.", S["cover_b"]))
    A(Spacer(1, 0.6 * cm))
    A(nota("Nunca compartas tu clave de Gemini. Se guarda únicamente en el archivo local.properties, "
           "que no debe subirse al repositorio.", "aviso"))

    A(NextPageTemplate("normal"))
    A(PageBreak())

    # ---------------- ÍNDICE ----------------
    A(Paragraph(E("Contenido"), S["h1x"]))
    A(P("El manual está pensado para leerse en orden la primera vez (instalación) y para consultarse "
        "por secciones después (uso diario y referencia)."))
    A(gap(8))
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"]]
    toc.dotsMinLevel = 0
    A(toc)
    A(PageBreak())

    # ---------------- 1. INTRODUCCIÓN ----------------
    A(h1("1. Introducción"))
    A(h2("1.1 Qué es WayCore"))
    A(PM("WayCore es la aplicación Android que funciona como centro de control del proyecto. Dentro de "
        "ella vive <b>Karbys</b>, un asistente de voz en español que responde por voz (TTS) y que puede "
        "consultar el estado real del teléfono (batería, hora, ubicación) y del dispositivo externo "
        "<b>WayHat</b>, un ESP32 con sensores de distancia, temperatura y humedad, pensado para apoyar "
        "la movilidad de personas con discapacidad visual."))
    A(PM("El proyecto está diseñado para que la interacción sea principalmente <b>por voz</b> y para que "
        "la seguridad <b>no dependa de Internet</b>: aunque no haya red o falle Gemini, WayHat sigue "
        "midiendo distancias y avisando con su buzzer de forma autónoma."))

    A(h2("1.2 Componentes del sistema"))
    A(tabla(
        ["Componente", "Qué es", "Dónde vive"],
        [
            [c("WayCore", "cellb"), c("Aplicación Android (Compose / Material 3) con la interfaz, los "
                                      "servicios en segundo plano y el cliente de Gemini."),
             cm_("app/src/main/java/com/wayhat/waycore/")],
            [c("Karbys", "cellb"), c("El asistente: escucha la palabra de activación, reconoce la voz, "
                                     "consulta a Gemini y habla la respuesta."), cm_("KarbysService.kt")],
            [c("WayHat", "cellb"), c("Dispositivo físico basado en ESP32-WROOM-32. Mide distancias con "
                                     "3 ultrasonidos y un TF-Luna, lee clima con un DHT11 y avisa con un buzzer."),
             cm_("WayHat_v6_WayCore.ino")],
            [c("Enlace Bluetooth", "cellb"), c("Servicio que mantiene el canal SPP con WayHat, recibe "
                                               "telemetría y envía comandos validados."), cm_("WayHatService.kt")],
            [c("Gemini", "cellb"), c("Modelo de lenguaje en la nube que razona la respuesta de Karbys y "
                                     "puede invocar herramientas para controlar WayHat."), cm_("GeminiClient.kt")],
            [c("Recordatorios", "cellb"), c("Alarmas programadas por voz que se guardan en preferencias y "
                                            "se disparan con AlarmManager."), cm_("ReminderReceiver.kt")],
        ],
        [2.7 * cm, 8.3 * cm, FRAME_W - 11.0 * cm]))

    A(h2("1.3 Cómo leer este manual"))
    A(bullets([
        "Las secciones 2, 3 y 4 describen las conexiones: arquitectura, cableado del hardware y enlaces lógicos.",
        "Las secciones 5 y 6 son de instalación y se siguen una sola vez.",
        "La sección 7 es el uso diario de la app.",
        "Las secciones 8 a 11 son de consulta y resolución de problemas.",
    ]))
    A(nota("Si solo quieres poner el sistema a funcionar: lee la sección 3 (cableado), la 6 (instalación) "
           "y la 7 (uso).", "ok"))

    A(PageBreak())

    # ---------------- 2. ARQUITECTURA ----------------
    A(h1("2. Arquitectura general y flujo de datos"))
    A(PM("Hay dos enlaces independientes que <b>no dependen entre sí</b>: el canal Bluetooth entre el "
        "teléfono y WayHat, y la conexión a Internet entre el teléfono y Gemini. Si Internet falla, "
        "WayHat sigue funcionando; si WayHat no está, Karbys sigue respondiendo con la información del "
        "teléfono."))
    A(gap(4))
    A(fig_arquitectura())
    A(Paragraph("Figura 1 — Flujo de datos entre sensores, WayHat, la app WayCore y Gemini.", S["caption"]))

    A(h2("2.1 Recorrido de una consulta por voz"))
    A(fig_flujo_voz())
    A(Paragraph("Figura 2 — Del hotword a la respuesta hablada.", S["caption"]))
    A(bullets([
        "Karbys permanece en escucha pasiva del hotword con resultados parciales, en español de México (es-MX).",
        "Al detectar la activación emite un pitido corto (beepStart) y abre una ventana de conversación de 6 segundos.",
        "El texto reconocido se compara primero con una lista de comandos locales (batería, hora, fecha, "
        "ubicación, alarmas y control de WayHat). Si coincide, se responde sin salir a Internet.",
        "Si no coincide, se construye un contexto fresco del dispositivo y se envía a Gemini junto con las "
        "últimas 4 intervenciones de la conversación.",
        "Gemini puede devolver texto o una llamada a herramienta (Function Calling). La herramienta se "
        "ejecuta en WayHatService, que la valida y espera la confirmación (ack) del ESP32.",
        "La respuesta final se pronuncia con TTS y se reabre la ventana de conversación para seguir hablando.",
    ]))

    A(h2("2.2 Regla de oro sobre los datos"))
    A(nota("Los valores de los sensores son la fuente de verdad. Karbys tiene instrucción explícita de no "
           "inventar ni redondear lecturas: si un sensor reporta -1, null o unavailable, debe decirlo tal cual.", "aviso"))

    A(PageBreak())

    # ---------------- 3. HARDWARE ----------------
    A(h1("3. Conexiones de hardware (WayHat / ESP32)"))
    A(PM("WayHat se construye sobre una placa <b>ESP32-WROOM-32</b> (módulo de 30 o 38 pines). El firmware "
        "usa Bluetooth Classic (SPP), por lo que <b>no sirve un ESP32-S2/S3/C3</b>: debe ser un ESP32 con "
        "Bluetooth clásico. Las conexiones siguientes se derivan directamente de las definiciones del "
        "archivo WayHat_v6_WayCore.ino."))

    A(h2("3.1 Lista de materiales"))
    A(tabla(
        ["Cant.", "Elemento", "Función"],
        [
            [c("1"), c("ESP32-WROOM-32 (DevKit)"), c("Cerebro de WayHat; lee sensores, decide el buzzer y expone el puerto serie Bluetooth.")],
            [c("3"), c("HC-SR04 (ultrasonido)"), c("Distancia derecha, izquierda y trasera.")],
            [c("1"), c("TF-Luna (LiDAR)"), c("Distancia frontal por láser; se usa con una zona de seguridad más amplia.")],
            [c("1"), c("DHT11"), c("Temperatura y humedad ambiental.")],
            [c("1"), c("Buzzer (activo o pasivo)"), c("Aviso sonoro de proximidad; se controla con tone()/noTone().")],
            [c("1"), c("Fuente de 5 V y cable USB"), c("Alimentación del ESP32 y de los sensores.")],
            [c("—"), c("Resistencias / divisor de nivel"), c("Recomendadas para adaptar ECHO de 5 V a los 3.3 V del ESP32.")],
        ],
        [1.4 * cm, 4.6 * cm, FRAME_W - 6.0 * cm]))

    A(h2("3.2 Mapa de pines"))
    A(P("Esta es la referencia exacta que usa el firmware. No la cambies sin cambiar también el archivo .ino."))
    A(tabla(
        ["GPIO", "Dirección", "Se conecta a", "Observación"],
        [
            [cm_("25", "cellcb"), c("Salida"), c("HC-SR04 DERECHO — TRIG"), c("Pulso de disparo de 10 us.")],
            [cm_("13", "cellcb"), c("Entrada"), c("HC-SR04 DERECHO — ECHO"), c("Entrada 3.3 V: usar divisor de nivel.")],
            [cm_("26", "cellcb"), c("Salida"), c("HC-SR04 IZQUIERDO — TRIG"), c("Pulso de disparo de 10 us.")],
            [cm_("14", "cellcb"), c("Entrada"), c("HC-SR04 IZQUIERDO — ECHO"), c("Entrada 3.3 V: usar divisor de nivel.")],
            [cm_("27", "cellcb"), c("Salida"), c("HC-SR04 TRASERO — TRIG"), c("Pulso de disparo de 10 us.")],
            [cm_("32", "cellcb"), c("Entrada"), c("HC-SR04 TRASERO — ECHO"), c("Entrada 3.3 V: usar divisor de nivel.")],
            [cm_("16", "cellcb"), c("Entrada (RX2)"), c("TF-Luna — TX"), c("Serial2 a 115200 8N1.")],
            [cm_("17", "cellcb"), c("Salida (TX2)"), c("TF-Luna — RX"), c("Serial2 a 115200 8N1.")],
            [cm_("33", "cellcb"), c("Bidireccional"), c("DHT11 — DATA"), c("Requiere resistencia pull-up de 4.7 kΩ a 10 kΩ.")],
            [cm_("4", "cellcb"), c("Salida"), c("Buzzer — terminal positivo"), c("tone() a 2100 Hz; negativo a GND.")],
            [cm_("5 V / VIN", "cellcb"), c("Alimentación"), c("HC-SR04 (los 3) y TF-Luna"), c("Los ultrasonidos necesitan 5 V.")],
            [cm_("3.3 V o 5 V", "cellcb"), c("Alimentación"), c("DHT11"), c("Según la presentación del módulo.")],
            [cm_("GND", "cellcb"), c("Tierra"), c("Todos los módulos"), c("Tierra común obligatoria.")],
        ],
        [2.4 * cm, 2.2 * cm, 4.6 * cm, FRAME_W - 9.2 * cm]))

    A(PageBreak())
    A(h2("3.3 Diagrama de cableado"))
    A(fig_cableado())
    A(Paragraph("Figura 3 — Conexionado completo de WayHat. Las líneas teal representan las señales; "
                "la alimentación (5 V y GND) es común a todos los módulos.", S["caption"]))

    A(h2("3.4 Cableado detallado por módulo"))

    A(h3("3.4.1 Ultrasónicos HC-SR04 (derecho, izquierdo y trasero)"))
    A(P("Cada sensor usa dos pines: el TRIG lo dispara el ESP32 y el ECHO devuelve un pulso cuya duración "
        "es proporcional a la distancia. El firmware mide hasta 25 ms de espera; si no hay eco devuelve -1."))
    A(code(
        "HC-SR04          ESP32\n"
        "-------------------------------\n"
        "VCC      ->      5 V (VIN)\n"
        "GND      ->      GND\n"
        "TRIG     ->      GPIO 25 / 26 / 27   (der. / izq. / tras.)\n"
        "ECHO     ->      divisor 5V->3.3V -> GPIO 13 / 14 / 32"))
    A(P("Divisor recomendado para ECHO: resistencia de 1 kΩ en serie con la señal y 2 kΩ a GND "
        "(o 2.2 kΩ / 3.3 kΩ). Sin divisor, el pin del ESP32 recibe 5 V y puede dañarse con el tiempo."))

    A(h3("3.4.2 TF-Luna (LiDAR frontal)"))
    A(P("Se comunica por UART a 115200 baudios usando el puerto serie 2 del ESP32. Ojo con el cruce: "
        "el TX del sensor va al RX del ESP32 y viceversa."))
    A(code(
        "TF-Luna          ESP32\n"
        "-------------------------------\n"
        "VCC (5 V)  ->    5 V (VIN)\n"
        "GND        ->    GND\n"
        "TX         ->    GPIO 16  (RX2 del ESP32)\n"
        "RX         ->    GPIO 17  (TX2 del ESP32)"))
    A(P("El firmware lee tramas de 9 bytes que empiezan con los dos bytes 0x59 y valida su checksum. "
        "Si la trama no llega o es inválida, la distancia queda en -1 y el campo tf_ok se reporta como false."))

    A(h3("3.4.3 DHT11 (temperatura y humedad)"))
    A(code(
        "DHT11            ESP32\n"
        "-------------------------------\n"
        "VCC        ->    3.3 V o 5 V (según módulo)\n"
        "DATA       ->    GPIO 33  (con pull-up 4.7k - 10k a VCC)\n"
        "GND        ->    GND"))
    A(P("Si la lectura falla, temp y hum se envían como null y dht_ok como false. Karbys lo reportará "
        "como dato no disponible en lugar de inventar un valor."))

    A(h3("3.4.4 Buzzer de aviso"))
    A(code(
        "BUZZER           ESP32\n"
        "-------------------------------\n"
        "+          ->    GPIO 4\n"
        "-          ->    GND"))
    A(P("El zumbador se activa con tone() a 2100 Hz en modo SAFE cuando la distancia más cercana es "
        "menor o igual a la sensibilidad. El intervalo entre pitidos se acorta a medida que el obstáculo "
        "se acerca (de 650 ms a 35 ms según el mapeo del firmware). La prueba manual usa 2200 Hz durante 250 ms."))

    A(h2("3.5 Notas eléctricas importantes"))
    A(bullets([
        "Todos los módulos deben compartir GND con el ESP32; sin tierra común las lecturas son erráticas.",
        "Los pines del ESP32 trabajan a 3.3 V. El ECHO de los HC-SR04 entrega 5 V: usa divisor de nivel.",
        "Si el buzzer consume más de ~20 mA, intercala un transistor (por ejemplo 2N2222) con una "
        "resistencia de base de 1 kΩ en lugar de conectarlo directo al GPIO.",
        "Mantén los cables del TF-Luna cortos y separados de los de los ultrasonidos para reducir ruido.",
        "Alimenta WayHat con una fuente estable: una caída de tensión provoca reinicios y lecturas en -1.",
    ]))

    A(PageBreak())

    # ---------------- 4. CONEXIONES LÓGICAS ----------------
    A(h1("4. Conexiones lógicas y de red"))
    A(P("Además del cableado, el sistema depende de tres canales de comunicación: Bluetooth SPP, el "
        "protocolo JSON propio y la API de Gemini. Esta sección documenta cada uno con los valores "
        "exactos que usa el código."))

    A(h2("4.1 Enlace Bluetooth SPP (teléfono ⇄ WayHat)"))
    A(tabla(
        ["Parámetro", "Valor"],
        [
            [c("Nombre del dispositivo", "cellb"), cm_("WayHat-Karbys")],
            [c("Tecnología", "cellb"), c("Bluetooth Classic, perfil Puerto Serie (SPP)")],
            [c("UUID del servicio", "cellb"), cm_("00001101-0000-1000-8000-00805F9B34FB")],
            [c("Vinculación", "cellb"), c("Debe estar emparejado desde Ajustes de Android antes de abrir la app.")],
            [c("Reconexión", "cellb"), c("Automática: reintenta cada 2500 ms si está desconectado y comprueba "
                                          "el estado cada 1000 ms si está conectado.")],
            [c("Estrategia de conexión", "cellb"),
             c("1) createRfcommSocketToServiceRecord → 2) createInsecureRfcommSocketToServiceRecord → "
               "3) createRfcommSocket(1) por reflexión.")],
            [c("Formato de línea", "cellb"), c("Un objeto JSON por línea terminada en salto de línea (\\n).")],
            [c("Confirmación de comandos", "cellb"), c("Cada comando incluye un id y espera un ack; "
                                                        "si no llega en 1800 ms se informa al asistente.")],
            [c("Telemetría", "cellb"), c("El ESP32 envía un JSON de telemetría cada 500 ms mientras haya cliente.")],
        ],
        [4.4 * cm, FRAME_W - 4.4 * cm]))
    A(nota("El teléfono debe aparecer en Ajustes → Bluetooth con el dispositivo «WayHat-Karbys» ya "
           "vinculado. La app no hace descubrimiento: busca el nombre entre los dispositivos emparejados.", "aviso"))

    A(h2("4.2 Protocolo JSON entre WayCore y WayHat"))

    A(h3("4.2.1 Telemetría: WayHat → teléfono (cada 500 ms)"))
    A(code(
        '{"type":"telemetry","available":true,"uptime_ms":12345,\n'
        ' "right":87,"left":-1,"rear":140,"tf":210,"closest":87,\n'
        ' "temp":26.0,"hum":61.0,"dht_ok":true,"threshold":50,\n'
        ' "mode":"SAFE","buzzer":true,"right_ok":true,"left_ok":false,\n'
        ' "rear_ok":true,"tf_ok":true}'))
    A(P("Significado de los campos:"))
    A(tabla(
        ["Campo", "Tipo", "Significado"],
        [
            [cm_("type"), c("texto"), c("Siempre \"telemetry\".")],
            [cm_("available"), c("booleano"), c("true cuando el ESP32 está operativo.")],
            [cm_("uptime_ms"), c("entero"), c("Milisegundos desde el arranque del ESP32.")],
            [cm_("right / left / rear"), c("entero"), c("Distancia en cm del HC-SR04 derecho, izquierdo y trasero. -1 = sin lectura.")],
            [cm_("tf"), c("entero"), c("Distancia en cm del TF-Luna. -1 = sin lectura.")],
            [cm_("closest"), c("entero"), c("Menor distancia válida entre los cuatro sensores. -1 = ninguna.")],
            [cm_("temp / hum"), c("decimal o null"), c("Temperatura (°C) y humedad (%) del DHT11.")],
            [cm_("dht_ok"), c("booleano"), c("true si el DHT11 respondió correctamente.")],
            [cm_("threshold"), c("entero"), c("Sensibilidad activa en cm (20 a 150).")],
            [cm_("mode"), c("texto"), c("\"SAFE\" con avisos de proximidad; \"CHAT\" silencia los avisos pero mantiene la telemetría.")],
            [cm_("buzzer"), c("booleano"), c("Estado de los avisos sonoros.")],
            [cm_("right_ok / left_ok"), c("booleano"), c("true si el sensor devolvió una distancia mayor a 0.")],
            [cm_("rear_ok / tf_ok"), c("booleano"), c("Mismo criterio para el trasero y el TF-Luna.")],
        ],
        [3.5 * cm, 2.2 * cm, FRAME_W - 5.7 * cm]))

    A(h3("4.2.2 Configuración: teléfono → WayHat"))
    A(P("Se usa para cambiar la sensibilidad, el modo y los avisos sonoros. En el ESP32 el valor de "
        "threshold se limita al rango 20–150 y los modos solo admiten SAFE o CHAT."))
    A(code(
        '{"type":"config","id":"k1730000000000_1","threshold":70,"mode":"SAFE","buzzer":true}'))

    A(h3("4.2.3 Comandos: teléfono → WayHat"))
    A(P("Solo existen estos nombres; cualquier otro devuelve error de lista blanca."))
    A(tabla(
        ["name", "Efecto en WayHat"],
        [
            [cm_("BUZZER_TEST"), c("Emite un pitido de prueba de 2200 Hz durante 250 ms.")],
            [cm_("SENSORS"), c("Fuerza una lectura inmediata de todos los sensores.")],
            [cm_("SAFE"), c("Activa el modo seguro (avisos de proximidad encendidos).")],
            [cm_("CHAT"), c("Activa el modo charla (silencia los avisos de proximidad).")],
        ],
        [3.4 * cm, FRAME_W - 3.4 * cm]))
    A(code('{"type":"command","id":"k1730000000000_2","name":"BUZZER_TEST"}'))

    A(h3("4.2.4 Confirmación: WayHat → teléfono"))
    A(code('{"type":"ack","id":"k1730000000000_1","ok":true,"message":"OK"}'))
    A(P("Si el comando no está permitido, ok llega como false y message indica el motivo "
        "(por ejemplo «Comando no permitido» o «Modo invalido»)."))

    A(PageBreak())
    A(h2("4.3 Conexión con Gemini"))
    A(tabla(
        ["Parámetro", "Valor"],
        [
            [c("Modelo", "cellb"), cm_("gemini-3.1-flash-lite")],
            [c("Endpoint", "cellb"), cm_("https://generativelanguage.googleapis.com/v1beta/models/\n"
                                          "gemini-3.1-flash-lite:generateContent")],
            [c("Autenticación", "cellb"), cm_("x-goog-api-key: TU_CLAVE")],
            [c("Método", "cellb"), c("POST con cuerpo JSON (contents + tools).")],
            [c("Tiempos de espera", "cellb"), c("Conexión 20 s, lectura 45 s, escritura 20 s.")],
            [c("Rondas de herramientas", "cellb"), c("Hasta 3 vueltas de Function Calling por consulta.")],
            [c("Memoria enviada", "cellb"), c("Últimas 4 intervenciones de la conversación.")],
        ],
        [4.2 * cm, FRAME_W - 4.2 * cm]))
    A(P("El contexto que se envía a Gemini incluye la hora local, la batería del teléfono, la ubicación "
        "(latitud, longitud, precisión y antigüedad) y la telemetría completa de WayHat. El sistema le "
        "indica explícitamente que esos datos son la fuente de verdad y que debe responder en español "
        "latinoamericano pensado para ser escuchado en voz alta, sin Markdown ni emojis."))

    A(h3("4.3.1 Herramientas disponibles (Function Calling)"))
    A(tabla(
        ["Herramienta", "Argumentos", "Qué hace"],
        [
            [cm_("set_wayhat_sensitivity"), cm_("centimeters (20-150)"), c("Cambia la distancia de activación de los avisos.")],
            [cm_("set_wayhat_mode"), cm_("mode: SAFE | CHAT"), c("Enciende o silencia los avisos de proximidad.")],
            [cm_("set_wayhat_alerts"), cm_("enabled: true | false"), c("Activa o desactiva el buzzer de WayHat.")],
            [cm_("test_wayhat_alert"), cm_("(ninguno)"), c("Pitido corto de prueba.")],
            [cm_("refresh_wayhat_telemetry"), cm_("(ninguno)"), c("Pide una lectura inmediata de sensores.")],
        ],
        [4.9 * cm, 4.1 * cm, FRAME_W - 9.0 * cm]))
    A(nota("Lista blanca estricta: Gemini no puede enviar comandos Bluetooth arbitrarios. Si pide algo "
           "fuera de estas cinco herramientas, WayHatService lo rechaza y Karbys informa de ello.", "ok"))

    A(h2("4.4 Servicios internos de la app"))
    A(tabla(
        ["Servicio", "Tipo", "Función"],
        [
            [cm_("KarbysService"), c("Primer plano · micrófono + ubicación"),
             c("Reconocimiento de voz, TTS, memoria corta, recordatorios y monitor de batería baja. "
               "Notificación persistente «Karbys está activo» (id 2401).")],
            [cm_("WayHatService"), c("Primer plano · dispositivo conectado"),
             c("Mantiene el socket SPP, recibe telemetría, ejecuta las herramientas permitidas y "
               "gestiona la vibración de seguridad. Notificación «Enlace Bluetooth con WayHat» (id 2601).")],
            [cm_("WayCoreService"), c("Primer plano"),
             c("Servicio auxiliar declarado en el manifiesto. Actualmente MainActivity no lo arranca: "
               "se conserva como base para futuras funciones.")],
            [cm_("ReminderReceiver"), c("BroadcastReceiver"),
             c("Recibe la alarma de un recordatorio y despierta a KarbysService para que lo anuncie por voz.")],
        ],
        [3.3 * cm, 4.0 * cm, FRAME_W - 7.3 * cm]))

    A(h2("4.5 Permisos de Android"))
    A(P("La app pide en tiempo de ejecución solo los permisos estrictamente necesarios; el resto quedan "
        "declarados en el manifiesto."))
    A(tabla(
        ["Permiso", "Se pide al usuario", "Para qué sirve"],
        [
            [cm_("RECORD_AUDIO"), c("Sí"), c("Reconocimiento de voz y hotword de Karbys.")],
            [cm_("ACCESS_COARSE_LOCATION"), c("Sí"), c("Ubicación aproximada para el contexto de Karbys.")],
            [cm_("ACCESS_FINE_LOCATION / BACKGROUND_LOCATION"), c("Declarados"), c("Ubicación precisa y en segundo plano.")],
            [cm_("BLUETOOTH_CONNECT / BLUETOOTH_SCAN"), c("Sí, en Android 12 o superior"), c("Conectar y buscar el dispositivo WayHat.")],
            [cm_("POST_NOTIFICATIONS"), c("Sí, en Android 13 o superior"), c("Mostrar las notificaciones de los servicios en primer plano.")],
            [cm_("INTERNET"), c("No (automático)"), c("Llamadas a la API de Gemini.")],
            [cm_("FOREGROUND_SERVICE (+ tipos)"), c("No (automático)"), c("Mantener Karbys y el enlace Bluetooth activos.")],
            [cm_("WAKE_LOCK / VIBRATE"), c("No (automático)"), c("No suspender el servicio y vibrar en los avisos de proximidad.")],
        ],
        [6.4 * cm, 3.2 * cm, FRAME_W - 9.6 * cm]))
    A(PM("Requisito de sistema: <b>Android 8.0 (API 26) o superior</b>; compilado con la API 35. Se "
        "recomienda un teléfono con Bluetooth clásico y motor de TTS en español instalado."))

    A(PageBreak())

    # ---------------- 5. REQUISITOS ----------------
    A(h1("5. Requisitos previos"))
    A(h2("5.1 Para el teléfono"))
    A(bullets([
        "Android 8.0 (API 26) o superior.",
        "Bluetooth clásico disponible y activado.",
        "Conexión a Internet para las respuestas de Gemini.",
        "Motor de texto a voz en español instalado (los servicios de Google TTS suelen incluirlo).",
        "Una clave de API de Gemini válida (Google AI Studio).",
    ]))
    A(h2("5.2 Para el equipo de desarrollo"))
    A(bullets([
        "Android Studio (Koala o superior) con el plugin de Kotlin y el Android SDK 35.",
        "JDK 17 (el proyecto compila con sourceCompatibility y targetCompatibility 17).",
        "Arduino IDE 2.x con el soporte de placas ESP32 (Espressif Systems) instalado.",
        "Librería DHT sensor library de Adafruit (junto con Adafruit Unified Sensor) para compilar el firmware.",
        "Cable USB de datos (no solo de carga) para flashear el ESP32.",
    ]))
    A(h2("5.3 Para el hardware"))
    A(bullets([
        "ESP32-WROOM-32 con Bluetooth clásico.",
        "Sensores, buzzer y cableado indicados en la sección 3.",
        "Fuente de 5 V estable o batería con capacidad suficiente.",
    ]))

    # ---------------- 6. INSTALACIÓN ----------------
    A(h1("6. Instalación y puesta en marcha"))
    A(P("El orden recomendado es: preparar la clave, cargar el firmware, instalar la app y por último "
        "vincular el Bluetooth. Así, cuando emparejes WayHat, la app ya estará lista para conectarse."))

    A(h2("6.1 Configurar la clave de Gemini"))
    A(PM("La clave <b>no</b> está incluida en el repositorio. Se inyecta en tiempo de compilación en el "
        "campo BuildConfig.GEMINI_API_KEY. El archivo local.properties <b>no debe subirse a Git</b>."))
    A(code(
        "# 1. Copia la plantilla\n"
        "cp local.properties.example local.properties\n\n"
        "# 2. Edita local.properties y sustituye el valor\n"
        "GEMINI_API_KEY=TU_CLAVE_DE_GEMINI"))
    A(P("No pongas comillas ni espacios alrededor de la clave. El script de Gradle limpia automáticamente "
        "comillas y saltos de línea accidentales, pero lo ideal es escribirla tal cual."))
    A(P("También puedes pasarla por línea de comandos o como propiedad de Gradle con el mismo nombre "
        "GEMINI_API_KEY; Gradle la detecta con providers.gradleProperty antes de leer local.properties."))
    A(nota("Si compilas sin clave, la app se instala igual, pero Karbys responderá «Falta configurar la "
           "clave de Gemini en WayCore» en cada consulta que no sea un comando local.", "aviso"))

    A(h2("6.2 Cargar el firmware en el ESP32"))
    A(bullets([
        "Abre WayHat_v6_WayCore.ino con Arduino IDE.",
        "Instala el soporte de placas ESP32 desde el Gestor de placas y selecciona «ESP32 Dev Module».",
        "Instala la librería DHT sensor library (Adafruit) y Adafruit Unified Sensor si te las pide.",
        "Conecta el ESP32 por USB y selecciona el puerto serie correspondiente.",
        "Deja la velocidad del monitor serie en 115200 baudios y sube el sketch.",
        "Al terminar, abre el monitor serie: debe imprimir «Bluetooth SPP listo: WayHat-Karbys» y "
        "«WAYHAT -> WAYCORE LISTO».",
    ]))
    A(P("Mensajes útiles del monitor serie: «WAYHAT: CELULAR CONECTADO» y «WAYHAT: CELULAR "
        "DESCONECTADO» confirman que el teléfono se está enlazando por Bluetooth."))

    A(h2("6.3 Compilar e instalar la app"))
    A(P("El repositorio no incluye el wrapper de Gradle, así que la forma más directa es abrirlo con "
        "Android Studio."))
    A(bullets([
        "Abre Android Studio y elige File → Open seleccionando la carpeta del repositorio.",
        "Espera a que Android Studio sincronice Gradle (usa Android Gradle Plugin 8.7.3 y Kotlin 2.0.21).",
        "Conecta el teléfono con la depuración USB activada o usa un emulador con Bluetooth real "
        "(para las pruebas de WayHat hace falta un dispositivo físico).",
        "Pulsa Run. El módulo es :app y el paquete es com.wayhat.waycore.",
    ]))
    A(P("Si prefieres línea de comandos, genera primero el wrapper y compila:"))
    A(code(
        "gradle wrapper --gradle-version 8.9\n"
        "./gradlew assembleDebug          # APK en app/build/outputs/apk/debug/\n"
        "./gradlew installDebug           # instala en el dispositivo conectado"))
    A(nota("Comprueba que local.properties existe antes de compilar; de lo contrario BuildConfig queda "
           "con la clave vacía y Karbys no podrá responder.", "aviso"))

    A(h2("6.4 Vincular WayHat por Bluetooth"))
    A(bullets([
        "Enciende WayHat (ESP32 alimentado).",
        "En el teléfono entra en Ajustes → Bluetooth y activa el Bluetooth.",
        "Busca «WayHat-Karbys» en dispositivos disponibles y empareja.",
        "Si el sistema pide un PIN, los valores habituales son 0000 o 1234.",
        "Abre WayCore: el servicio intentará la conexión SPP automáticamente.",
    ]))
    A(P("La app no escanea dispositivos nuevos: solo busca el nombre exacto entre los ya emparejados. "
        "Si cambias el nombre en el firmware, debes cambiar también DEVICE_NAME en WayHatService.kt."))

    A(h2("6.5 Primer arranque y permisos"))
    A(bullets([
        "Al abrir WayCore por primera vez se solicitan micrófono, ubicación aproximada, Bluetooth y "
        "notificaciones (según la versión de Android).",
        "Concede el micrófono: sin él Karbys queda en pausa y aparece el botón ACTIVAR KARBYS.",
        "Concede Bluetooth en Android 12 o superior; de lo contrario el estado será «Permiso Bluetooth pendiente».",
        "Concede notificaciones para que los servicios en primer plano se muestren correctamente.",
        "Si niegas un permiso por error, puedes reactivarlo desde Ajustes del sistema o con el botón "
        "ACTIVAR KARBYS dentro de la app.",
    ]))

    A(PageBreak())

    # ---------------- 7. USO ----------------
    A(h1("7. Uso de la aplicación"))
    A(P("La pantalla principal está pensada para ser legible y accionable con lector de pantalla: cada "
        "control tiene descripción de contenido y la información importante se muestra como texto."))

    A(h2("7.1 Pantalla principal"))
    A(tabla(
        ["Elemento", "Qué hace"],
        [
            [c("Título WAYCORE y estado de WayHat", "cellb"),
             c("Indica si WayHat está conectado o muestra el último mensaje del enlace "
               "(por ejemplo «Vincula WayHat-Karbys en Bluetooth»).")],
            [c("Botón grande HABLAR", "cellb"),
             c("Abre una escucha directa sin esperar el hotword. Si Karbys está en pausa, el botón "
               "muestra KARBYS y sirve para activarlo.")],
            [c("Campo de texto + ENVIAR", "cellb"),
             c("Permite escribir la pregunta en lugar de dictarla. Útil en lugares con ruido.")],
            [c("Modo SEGURO / CHARLA", "cellb"),
             c("SEGURO mantiene los avisos de proximidad; CHARLA los silencia para conversar, pero "
               "mantiene la telemetría y las lecturas.")],
            [c("Deslizador de sensibilidad", "cellb"),
             c("Ajusta la distancia de aviso entre 20 y 100 cm, en pasos de 5 cm. El firmware acepta "
               "hasta 150 cm por comando de voz o desde Gemini.")],
            [c("Interruptor de avisos sonoros", "cellb"),
             c("Activa o desactiva el buzzer de WayHat. No afecta a la voz de Karbys.")],
            [c("Lecturas de distancia", "cellb"),
             c("Derecha, izquierda, atrás, TF-Luna y la distancia más cercana. Un guion «—» significa "
               "sin lectura válida (-1).")],
            [c("Batería y GPS", "cellb"),
             c("Nivel de batería del teléfono y última ubicación conocida en formato latitud, longitud.")],
            [c("RECONECTAR WAYHAT", "cellb"),
             c("Fuerza un intento de conexión inmediato sin esperar el ciclo automático de 2.5 s.")],
            [c("PROBAR BUZZER", "cellb"),
             c("Envía BUZZER_TEST: un pitido de 2200 Hz de 250 ms para verificar el zumbador.")],
            [c("ACTUALIZAR", "cellb"),
             c("Envía SENSORS: obliga al ESP32 a releer todos los sensores al instante.")],
            [c("ACTIVAR KARBYS", "cellb"),
             c("Aparece solo si Karbys está en pausa por falta de permiso de micrófono.")],
        ],
        [5.0 * cm, FRAME_W - 5.0 * cm]))

    A(h2("7.2 Hablar con Karbys"))
    A(P("Karbys escucha de tres formas:"))
    A(bullets([
        "Por palabra de activación: di «Oye Karbys» seguido de tu pregunta.",
        "Con el botón HABLAR de la pantalla principal.",
        "Escribiendo la pregunta en el campo de texto y pulsando ENVIAR.",
    ]))
    A(P("El detector acepta variantes de la palabra de activación y del nombre, porque el reconocedor "
        "suele cambiar la ortografía: oye, hey, ey, ei, oiga, hola + karbys, karvis, karbis, carvis, "
        "carbis, carbys, karvys, carvys, karby, karvy, carby, carvy. También se acepta el nombre solo."))
    A(P("Después de cada respuesta, Karbys queda a la escucha durante 6 segundos (silencio máximo de "
        "4.5 s) para que puedas continuar la conversación sin repetir la palabra de activación. Al "
        "terminar la ventana vuelve al modo de espera del hotword."))
    A(nota("Si hay un auricular Bluetooth o con cable conectado, Karbys redirige el audio al auricular "
           "para escuchar y hablar mejor.", "ok"))

    A(h2("7.3 Comandos de voz disponibles"))
    A(P("Estos comandos se resuelven en el propio teléfono, sin depender de Gemini ni de Internet:"))
    A(tabla(
        ["Di algo como...", "Respuesta de Karbys"],
        [
            [c("¿Cuánta batería tengo?"), c("Indica el porcentaje de batería del teléfono.")],
            [c("¿Qué hora es?"), c("Da la hora local en formato de 12 horas.")],
            [c("¿Qué día es hoy? / ¿Qué fecha es?"), c("Indica la fecha completa en español.")],
            [c("¿Dónde estoy?"), c("Lee latitud y longitud de la última ubicación conocida.")],
            [c("Pausa Karbys / Silencio Karbys"), c("Deja al asistente en pausa hasta que digas «Oye Karbys».")],
            [c("Recuérdame estudiar a las siete de la tarde"), c("Programa un recordatorio por voz.")],
            [c("Pon una alarma en 20 minutos"), c("Programa un recordatorio relativo.")],
            [c("Mis tareas / Mis recordatorios"), c("Enumera los recordatorios pendientes.")],
            [c("Cancela todas las alarmas"), c("Borra todos los recordatorios programados.")],
            [c("Modo seguro / Modo charla"), c("Cambia WayHat entre SAFE y CHAT.")],
            [c("Activa los avisos / Activa el buzzer"), c("Enciende los avisos sonoros de WayHat.")],
            [c("Desactiva los avisos / Desactiva el sonido"), c("Apaga el buzzer de WayHat.")],
            [c("Sensibilidad en 80"), c("Cambia la distancia de aviso a 80 cm.")],
            [c("Estado de WayHat / Sensores de WayHat"), c("Lee la telemetría más reciente.")],
            [c("Actualiza los sensores"), c("Pide una lectura inmediata al ESP32.")],
            [c("Prueba el buzzer"), c("Emite el pitido de prueba.")],
        ],
        [6.6 * cm, FRAME_W - 6.6 * cm]))
    A(P("Cualquier otra frase se envía a Gemini junto con el contexto del dispositivo."))

    A(h2("7.4 Recordatorios y alarmas"))
    A(bullets([
        "Formatos aceptados: «a las 7 de la tarde», «a las 7:30», «a las 8 am/pm» y «en 20 minutos» "
        "o «en 2 horas».",
        "Si la hora ya pasó hoy, el recordatorio se programa para el día siguiente. Si dices «mañana», "
        "se suma un día.",
        "Los recordatorios se guardan en las preferencias del teléfono y se disparan con AlarmManager; "
        "al sonar, Karbys emite un tono de alerta y anuncia el recordatorio por voz.",
        "Karbys también avisa por voz cuando la batería del teléfono baja a 5 % o menos.",
    ]))
    A(nota("El manifiesto declara RECEIVE_BOOT_COMPLETED, pero todavía no hay un receptor de arranque "
           "implementado: los recordatorios no sobreviven a un reinicio del teléfono. Tenlo presente "
           "si vas a apagar el equipo.", "aviso"))

    A(h2("7.5 Avisos de proximidad y vibración"))
    A(bullets([
        "En modo SAFE, WayHat hace sonar el buzzer cuando la distancia más cercana es menor o igual a "
        "la sensibilidad configurada, con un intervalo que se acorta al acercarse el obstáculo.",
        "El teléfono vibra además cuando algún sensor entra en zona de peligro, con un mínimo de 350 ms "
        "entre vibraciones para que no resulte molesto.",
        "El TF-Luna usa una zona de seguridad más amplia: como mínimo 100 cm, o la sensibilidad si esta "
        "es mayor. Es intencional, porque su alcance es mayor que el de los HC-SR04.",
        "En modo CHAT no hay pitidos ni vibración de proximidad, pero la telemetría sigue actualizándose "
        "y puedes consultarla cuando quieras.",
    ]))

    A(h2("7.6 Servicios en segundo plano"))
    A(P("Mientras la app está abierta o en segundo plano verás dos notificaciones permanentes: "
        "«Karbys está activo» y «Enlace Bluetooth con WayHat». Son necesarias para que el "
        "micrófono y el socket Bluetooth sigan funcionando. Si cierras la app por completo, los "
        "servicios se detienen hasta que la vuelvas a abrir."))

    A(PageBreak())

    # ---------------- 8. REFERENCIA RÁPIDA ----------------
    A(h1("8. Referencia rápida"))
    A(h2("8.1 Puesta en marcha en 6 pasos"))
    A(code(
        "1. Cablea WayHat según la sección 3 (pines 25/13, 26/14, 27/32, 16/17, 33, 4).\n"
        "2. Sube WayHat_v6_WayCore.ino al ESP32 y verifica el monitor serie a 115200.\n"
        "3. cp local.properties.example local.properties  ->  pega tu GEMINI_API_KEY.\n"
        "4. Abre el proyecto en Android Studio y ejecuta Run (módulo :app).\n"
        "5. Empareja 'WayHat-Karbys' en Ajustes -> Bluetooth del teléfono.\n"
        "6. Abre WayCore, concede permisos y di: 'Oye Karbys, estado de WayHat'."))
    A(h2("8.2 Resumen de pines de WayHat"))
    A(code(
        "DERECHO   TRIG 25   ECHO 13\n"
        "IZQUIERDO TRIG 26   ECHO 14\n"
        "TRASERO   TRIG 27   ECHO 32\n"
        "TF-Luna   TX->16    RX<-17   (Serial2 @115200)\n"
        "DHT11     DATA  33\n"
        "BUZZER    GPIO  4\n"
        "Bluetooth WayHat-Karbys   SPP 00001101-0000-1000-8000-00805F9B34FB"))
    A(h2("8.3 Ciclos de tiempo del firmware"))
    A(tabla(
        ["Acción", "Cadencia"],
        [
            [c("Lectura de sensores"), c("Cada 250 ms")],
            [c("Envío de telemetría"), c("Cada 500 ms (solo si hay cliente Bluetooth)")],
            [c("Reintento de conexión"), c("Cada 2500 ms si está desconectado")],
            [c("Espera de confirmación (ack)"), c("1800 ms")],
            [c("Ventana de conversación"), c("6000 ms tras la respuesta de Karbys")],
            [c("Silencio para cerrar la escucha"), c("4500 ms")],
        ],
        [6.4 * cm, FRAME_W - 6.4 * cm]))

    # ---------------- 9. SOLUCIÓN DE PROBLEMAS ----------------
    A(h1("9. Solución de problemas"))
    A(tabla(
        ["Síntoma", "Causa probable", "Qué hacer"],
        [
            [c("Estado: «Vincula WayHat-Karbys en Bluetooth»"),
             c("El dispositivo no está emparejado o el nombre no coincide."),
             c("Empareja «WayHat-Karbys» en Ajustes. Revisa BT_NAME en el .ino y DEVICE_NAME en WayHatService.kt.")],
            [c("Estado: «Bluetooth está apagado»"),
             c("El radio Bluetooth del teléfono está desactivado."),
             c("Actívalo y pulsa RECONECTAR WAYHAT.")],
            [c("Estado: «Permiso Bluetooth pendiente»"),
             c("Falta BLUETOOTH_CONNECT en Android 12 o superior."),
             c("Concede el permiso en Ajustes → Aplicaciones → WayCore → Permisos.")],
            [c("«No se pudo conectar; reintentando…» de forma continua"),
             c("El socket SPP está ocupado por otra app o el ESP32 se reinicia."),
             c("Cierra otras apps de terminal Bluetooth, reinicia el ESP32 y vuelve a intentarlo. "
               "La app prueba tres métodos de conexión automáticamente.")],
            [c("Las distancias aparecen como «—»"),
             c("Lectura -1: sensor sin eco, desconectado o con error de checksum."),
             c("Revisa cableado y alimentación. Usa ACTUALIZAR para forzar una lectura y mira el monitor "
               "serie a 115200.")],
            [c("Temperatura o humedad siempre no disponibles"),
             c("El DHT11 no responde o falta la resistencia pull-up."),
             c("Añade una pull-up de 4.7 kΩ a 10 kΩ en DATA y verifica VCC y GND.")],
            [c("El TF-Luna no da lectura"),
             c("Cruce de pines o velocidad incorrecta."),
             c("Conecta TX del sensor al GPIO 16 y RX al GPIO 17, a 115200 baudios.")],
            [c("Karbys no responde al hotword"),
             c("Falta permiso de micrófono, ruido ambiente o el reconocedor no reconoce el nombre."),
             c("Concede el micrófono, usa el botón HABLAR o el campo de texto, y habla cerca del teléfono.")],
            [c("Karbys dice «Falta configurar la clave de Gemini»"),
             c("local.properties sin GEMINI_API_KEY o compilado antes de crearlo."),
             c("Crea el archivo con tu clave, haz Clean Project y vuelve a compilar e instalar.")],
            [c("Karbys dice «No pude conectar con Gemini»"),
             c("Sin Internet o la API devolvió un error."),
             c("Verifica la conexión y que la clave tenga el modelo habilitado; vuelve a intentarlo.")],
            [c("Karbys no ejecuta un cambio en WayHat"),
             c("WayHat desconectado, valor fuera de rango o herramienta no permitida."),
             c("Revisa el estado del enlace. La sensibilidad debe estar entre 20 y 150 cm y el modo "
               "debe ser SAFE o CHAT.")],
            [c("El buzzer no suena en modo SEGURO"),
             c("Avisos desactivados, distancia por encima del umbral o cableado del zumbador."),
             c("Activa el interruptor de avisos y pulsa PROBAR BUZZER para comprobar el zumbador.")],
            [c("La app se cierra o el asistente se detiene"),
             c("El sistema limitó los servicios en segundo plano."),
             c("Desactiva la optimización de batería para WayCore y mantén la app en uso reciente.")],
            [c("Gran consumo de batería"),
             c("Escucha continua del hotword, Bluetooth y GPS activos."),
             c("Es esperable: el hotword requiere micrófono permanente. Usa «Pausa Karbys» cuando no lo necesites.")],
        ],
        [4.6 * cm, 4.4 * cm, FRAME_W - 9.0 * cm]))

    A(PageBreak())

    # ---------------- 10. SEGURIDAD ----------------
    A(h1("10. Seguridad, límites y buenas prácticas"))
    A(h2("10.1 Seguridad del sistema"))
    A(bullets([
        "Lista blanca de comandos: el ESP32 solo acepta los tipos «config» y «command» y rechaza "
        "cualquier otro con un ack en false.",
        "Validación de rangos: la sensibilidad se limita a 20–150 cm y el modo solo admite SAFE o CHAT.",
        "Confirmación: cada comando lleva un id y el ESP32 responde con un ack antes de que Karbys "
        "confirme la acción en voz alta.",
        "Independencia de la red: la seguridad local de WayHat funciona sin Gemini y sin Internet.",
        "Datos reales: el sistema instruye a Karbys para no inventar lecturas de sensores ni estados.",
    ]))
    A(h2("10.2 Límites actuales"))
    A(bullets([
        "El deslizador de la app llega a 100 cm, aunque el firmware acepta hasta 150 cm; ese valor "
        "superior solo se alcanza por voz o mediante Gemini.",
        "La telemetría depende de la última trama recibida: si se pierde el enlace, la app conserva la "
        "última lectura válida en pantalla.",
        "Los recordatorios no sobreviven al reinicio del teléfono (no hay receptor de arranque implementado).",
        "WayCoreService está declarado en el manifiesto pero no se utiliza desde MainActivity.",
        "El número de versión no es consistente entre archivos: el README menciona v0.5.0, el Gradle "
        "declara versionName 0.3.0 con versionCode 6, y el firmware se llama v6. Conviene unificarlo.",
        "Karbys no controla música ni otras aplicaciones.",
    ]))
    A(h2("10.3 Buenas prácticas"))
    A(bullets([
        "No subas local.properties al repositorio; añádelo a .gitignore (el proyecto aún no lo incluye).",
        "Prueba siempre el sistema en un entorno controlado antes de usarlo en la calle.",
        "El asistente apoya la movilidad, pero no sustituye al bastón ni a las técnicas de orientación.",
        "Verifica periódicamente el estado de los sensores con «Estado de WayHat».",
        "Mantén el ESP32 alimentado de forma estable y revisa el cableado si aparecen lecturas en -1.",
    ]))

    # ---------------- 11. CRÉDITOS ----------------
    A(h1("11. Créditos"))
    A(P("El proyecto fue creado con amor y cariño para todos. WayCore es un producto de WayCorp y Karbys "
        "vive dentro de él."))
    A(tabla(
        ["Persona", "Rol"],
        [
            [c("Danny Joel Castro Juárez", "cellb"),
             c("Estudiante de primer año de Desarrollo de Software en el Instituto Nacional de San Miguel "
               "Tepezontes. Lidera el desarrollo de software, WayCore y la integración de Karbys.")],
            [c("Dennis Alexander", "cellb"), c("Desarrollador de hardware.")],
            [c("Daylin Odalis", "cellb"), c("Secretaria, portavoz, documentadora y responsable de verificación de procesos.")],
            [c("Emely Denisse", "cellb"), c("Diseñadora y documentadora.")],
            [c("Licda. Gloria Yessenia Mármol de Muñoz", "cellb"),
             c("Agradecimiento especial por su dedicación para enseñarles esta carrera técnica.")],
        ],
        [5.4 * cm, FRAME_W - 5.4 * cm]))
    A(gap(8))
    A(nota("Este manual se genera automáticamente con docs/generar_manual.py a partir del código del "
           "repositorio. Si cambias pines, nombres, mensajes o endpoints, vuelve a generarlo para que "
           "la documentación no quede desactualizada.", "ok"))

    # ---------------- ANEXO ----------------
    A(PageBreak())
    A(h1("Anexo A — Mensajes de estado del enlace Bluetooth"))
    A(P("Estos son los textos que puede mostrar la parte superior de la pantalla, tal como los emite "
        "WayHatService. Sirven para diagnosticar el estado del enlace de un vistazo."))
    A(tabla(
        ["Mensaje", "Qué significa"],
        [
            [c("Iniciando enlace Bluetooth…", "cellb"), c("El servicio acaba de arrancar y todavía no ha intentado conectar.")],
            [c("Permiso Bluetooth pendiente", "cellb"), c("Falta BLUETOOTH_CONNECT en Android 12 o superior.")],
            [c("Este celular no tiene Bluetooth Classic", "cellb"), c("El hardware del teléfono no soporta el perfil SPP.")],
            [c("Bluetooth está apagado", "cellb"), c("Activa el Bluetooth del teléfono.")],
            [c("Vincula WayHat-Karbys en Bluetooth", "cellb"), c("No hay ningún dispositivo emparejado con ese nombre.")],
            [c("WayHat vinculado: abriendo conexión SPP…", "cellb"), c("Encontró el dispositivo y está abriendo el socket.")],
            [c("WayHat conectado por Bluetooth", "cellb"), c("Enlace establecido; la telemetría ya fluye.")],
            [c("No se pudo conectar; reintentando…", "cellb"), c("Fallaron los tres métodos de conexión; reintentará en 2.5 s.")],
            [c("WayHat desconectado; reconectando…", "cellb"), c("Se perdió el enlace durante la lectura.")],
            [c("WayHat aún no está conectado", "cellb"), c("Se intentó enviar un comando sin enlace activo.")],
        ],
        [6.6 * cm, FRAME_W - 6.6 * cm]))

    A(h1("Anexo B — Glosario"))
    A(tabla(
        ["Término", "Significado"],
        [
            [c("SPP", "cellb"), c("Serial Port Profile: emulación de un puerto serie sobre Bluetooth clásico.")],
            [c("Telemetría", "cellb"), c("Paquete JSON con el estado completo de los sensores de WayHat.")],
            [c("ack", "cellb"), c("Mensaje de confirmación que devuelve el ESP32 tras ejecutar un comando.")],
            [c("Hotword", "cellb"), c("Palabra de activación que despierta a Karbys («Oye Karbys»).")],
            [c("Function Calling", "cellb"), c("Mecanismo con el que Gemini pide ejecutar una herramienta "
                                               " concreta del dispositivo.")],
            [c("TF-Luna", "cellb"), c("Sensor de distancia por láser (LiDAR) de mayor alcance que el HC-SR04.")],
            [c("TTS", "cellb"), c("Texto a voz: el motor que pronuncia las respuestas de Karbys.")],
            [c("BuildConfig", "cellb"), c("Clase generada por Gradle donde se inyecta GEMINI_API_KEY.")],
        ],
        [3.6 * cm, FRAME_W - 3.6 * cm]))

    return s


# ----------------------------------------------------------------------------
# Construcción
# ----------------------------------------------------------------------------
def main():
    doc = ManualDoc(
        OUT_PDF,
        pagesize=A4,
        leftMargin=M_LEFT, rightMargin=M_RIGHT,
        topMargin=M_TOP, bottomMargin=M_BOTTOM,
        title="WayCore + WayHat - Manual de uso, instalación y conexiones",
        author="WayCorp · Danny Joel Castro Juárez y equipo",
        subject="Asistente Karbys · ESP32 · Bluetooth SPP · Gemini",
        creator="docs/generar_manual.py",
    )

    frame_portada = Frame(M_LEFT, M_BOTTOM, FRAME_W, FRAME_H, id="portada",
                          leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_normal = Frame(M_LEFT, M_BOTTOM, FRAME_W, FRAME_H, id="normal",
                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[frame_portada], onPage=fondo_portada),
        PageTemplate(id="normal", frames=[frame_normal], onPage=fondo_normal),
    ])

    doc.multiBuild(construir_story())
    print("PDF generado: %s (%.1f KB)" % (OUT_PDF, os.path.getsize(OUT_PDF) / 1024.0))


if __name__ == "__main__":
    main()
