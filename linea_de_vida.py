import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from sympy import symbols, lambdify, sympify
from fpdf import FPDF
import io
import csv
import tempfile

# ====================== FUNCIONES BASE ======================

def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    for i in range(1, len(anclajes)):
        longitud += calcular_distancia(anclajes[i - 1], anclajes[i])
    return longitud

def segmento_dentro_rango(p1, p2, f_lambdified, paso=0.1, max_sep=0.5):
    num_pasos = max(2, int(calcular_distancia(p1, p2) / paso))
    for i in range(1, num_pasos):
        t = i / num_pasos
        x = p1[0] + t * (p2[0] - p1[0])
        y = p1[1] + t * (p2[1] - p1[1])
        y_func = f_lambdified(x)
        if y - y_func < 0 or y - y_func > max_sep:
            return False
    return True

def generar_puntos_funcion(expr, x_min, x_max, distancia_maxima):
    x = symbols('x')
    f_expr = sympify(expr)
    f_lambdified = lambdify(x, f_expr, 'numpy')

    puntos = []
    anclajes = []
    x_actual = x_min

    while x_actual <= x_max:
        y_actual = float(f_lambdified(x_actual)) + 0.1  # Siempre 0.1 m por encima
        puntos.append((x_actual, float(f_lambdified(x_actual))))
        anclajes.append((x_actual, y_actual))
        x_actual += 0.1  # Siempre separados 0.1 m

    # Filtrar anclajes para tener los mínimos necesarios
    anclajes_filtrados = [anclajes[0]]
    i = 0
    while i < len(anclajes) - 1:
        j = i + 1
        while j < len(anclajes) and calcular_distancia(anclajes[i], anclajes[j]) <= distancia_maxima:
            if segmento_dentro_rango(anclajes[i], anclajes[j], f_lambdified, paso=0.1, max_sep=0.5):
                j += 1
            else:
                break
        anclajes_filtrados.append(anclajes[j - 1])
        i = j - 1

    longitud_linea_vida = calcular_longitud_linea_vida(anclajes_filtrados)
    return puntos, anclajes_filtrados, longitud_linea_vida

def generar_puntos_desde_lista(lista_puntos, distancia_maxima):
    anclajes = [lista_puntos[0]]
    for i in range(1, len(lista_puntos)):
        p1, p2 = np.array(lista_puntos[i - 1]), np.array(lista_puntos[i])
        segmento = p2 - p1
        distancia_segmento = np.linalg.norm(segmento)
        num_interpolaciones = math.floor(distancia_segmento / distancia_maxima)
        for j in range(1, num_interpolaciones + 1):
            punto_interpolado = p1 + segmento * (j * distancia_maxima / distancia_segmento)
            anclajes.append(tuple(punto_interpolado))
        anclajes.append(tuple(p2))
    longitud_linea_vida = calcular_longitud_linea_vida(anclajes)
    return anclajes, longitud_linea_vida

def exportar_pdf(anclajes, posiciones, img_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte de Anclajes", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(60, 10, "x", 1)
    pdf.cell(60, 10, "y", 1)
    pdf.cell(60, 10, "posición (m)", 1)
    pdf.ln()

    for a, p in zip(anclajes, posiciones):
        pdf.cell(60, 10, f"{a[0]:.2f}", 1)
        pdf.cell(60, 10, f"{a[1]:.2f}", 1)
        pdf.cell(60, 10, f"{p:.2f}", 1)
        pdf.ln()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        tmp_img.write(img_data)
        tmp_img.flush()
        pdf.image(tmp_img.name, x=10, y=None, w=180)

    return pdf.output(dest='S').encode('latin1')

# ====================== INTERFAZ STREAMLIT ======================

st.title("Diseñador de Línea de Vida para Trabajo en Altura")
modo = st.selectbox("Modo de entrada", ["Función", "Lista de puntos"])
distancia_maxima = st.number_input("Distancia máxima entre anclajes (m)", min_value=0.1, value=5.0)

if modo == "Función":
    expr = st.text_input("Introduce la función (en x)", "sin(x) * 3 + 5")
    x_min = st.number_input("Valor mínimo de x", value=0.0)
    x_max = st.number_input("Valor máximo de x", value=20.0)

    if x_max > x_min:
        puntos, anclajes, longitud_linea_vida = generar_puntos_funcion(expr, x_min, x_max, distancia_maxima)

        posiciones = [0.0]
        for i in range(1, len(anclajes)):
            posiciones.append(posiciones[-1] + calcular_distancia(anclajes[i - 1], anclajes[i]))

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        for a, p in zip(anclajes, posiciones):
            st.write(f"x = {a[0]:.2f}, y = {a[1]:.2f}, posición = {p:.2f} m")

        x_p, y_p = zip(*puntos)
        x_a, y_a = zip(*anclajes)

        fig, ax = plt.subplots()
        ax.plot(x_p, y_p, label="Silueta (función)", color='gray')
        ax.plot(x_a, y_a, 'o-', label="Línea de vida", color='red')
        ax.set_title("Línea de vida sobre función")
        ax.set_aspect('equal')
        ax.grid(True)
        ax.legend()

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        st.pyplot(fig)

        # CSV
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(["x", "y", "posición"])
        for a, p in zip(anclajes, posiciones):
            csv_writer.writerow([f"{a[0]:.2f}", f"{a[1]:.2f}", f"{p:.2f}"])
        st.download_button("📥 Descargar CSV", csv_buffer.getvalue(), file_name="anclajes.csv", mime="text/csv")

        # PDF
        pdf_bytes = exportar_pdf(anclajes, posiciones, buf.getvalue())
        st.download_button("📄 Descargar PDF", pdf_bytes, file_name="reporte_linea_vida.pdf", mime="application/pdf")

elif modo == "Lista de puntos":
    texto_puntos = st.text_area("Introduce puntos como [(x1, y1), (x2, y2), ...]", "[(0, 0), (5, 2), (9, 2), (12, 6)]")
    try:
        lista_puntos = eval(texto_puntos)
        anclajes, longitud_linea_vida = generar_puntos_desde_lista(lista_puntos, distancia_maxima)

        posiciones = [0.0]
        for i in range(1, len(anclajes)):
            posiciones.append(posiciones[-1] + calcular_distancia(anclajes[i - 1], anclajes[i]))

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        for a, p in zip(anclajes, posiciones):
            st.write(f"x = {a[0]:.2f}, y = {a[1]:.2f}, posición = {p:.2f} m")

        x_p, y_p = zip(*lista_puntos)
        x_a, y_a = zip(*anclajes)

        fig, ax = plt.subplots()
        ax.plot(x_p, y_p, '--', label="Silueta (puntos)", color='
