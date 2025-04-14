import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, lambdify, sympify
from fpdf import FPDF
import io
import csv
import tempfile

# --------------------------------
# Utilidades de cálculo
# --------------------------------
def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    for i in range(1, len(anclajes)):
        longitud += calcular_distancia(anclajes[i - 1], anclajes[i])
    return longitud


def distancia_punto_a_funcion(f, x0, y0):
    y_func = f(x0)
    return abs(y0 - y_func)


def generar_anclajes_funcion(expr, x_min, x_max, dist_max_entre_puntos=0.1, dist_max_a_funcion=0.5):
    x = symbols('x')
    f_sym = sympify(expr)
    f = lambdify(x, f_sym, 'numpy')

    puntos = []
    x_vals = np.arange(x_min, x_max + dist_max_entre_puntos, dist_max_entre_puntos)
    y_vals = f(x_vals)
    for xi, yi in zip(x_vals, y_vals):
        puntos.append((xi, yi))

    anclajes = [puntos[0]]
    i = 0
    while i < len(puntos) - 1:
        for j in range(len(puntos) - 1, i, -1):
            xi, yi = puntos[i]
            xj, yj = puntos[j]

            # Verificamos si la recta entre puntos i y j se mantiene por encima de la función
            n_check = 20
            inter_x = np.linspace(xi, xj, n_check)
            inter_y = np.linspace(yi, yj, n_check)
            y_func_vals = f(inter_x)

            diffs = inter_y - y_func_vals
            if np.all(diffs >= 0) and np.max(diffs) <= dist_max_a_funcion:
                anclajes.append((xj, yj))
                i = j
                break
        else:
            i += 1  # En caso de no encontrar un punto válido, avanzar

    longitud_total = calcular_longitud_linea_vida(anclajes)

    return puntos, anclajes, longitud_total


# --------------------------------
# Exportar a PDF
# --------------------------------
def exportar_pdf(anclajes, posiciones, img_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte de Anclajes - Línea de Vida", ln=True, align='C')
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

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes


# --------------------------------
# STREAMLIT APP
# --------------------------------
st.title("Diseñador de Línea de Vida para Trabajo en Altura")

expr = st.text_input("Introduce la función (en x)", "sin(x) * 3 + 5")
x_min = st.number_input("Valor mínimo de x", value=0.0)
x_max = st.number_input("Valor máximo de x", value=20.0)
dist_max_anclajes = st.number_input("Separación máxima entre puntos de prueba (m)", value=0.1)
dist_max_a_funcion = st.number_input("Separación máxima a la cornisa (m)", value=0.5)

if x_max > x_min:
    puntos, anclajes, longitud = generar_anclajes_funcion(expr, x_min, x_max, dist_max_anclajes, dist_max_a_funcion)

    posiciones = [0.0]
    for i in range(1, len(anclajes)):
        posiciones.append(posiciones[-1] + calcular_distancia(anclajes[i - 1], anclajes[i]))

    st.write(f"🔩 Total de anclajes: {len(anclajes)}")
    st.write(f"📏 Longitud total de la línea de vida: {longitud:.2f} metros")

    st.write("📍 Coordenadas de anclajes:")
    for a, p in zip(anclajes, posiciones):
        st.write(f"x = {a[0]:.2f}, y = {a[1]:.2f}, posición = {p:.2f} m")

    # Gráfica
    x_p, y_p = zip(*puntos)
    x_a, y_a = zip(*anclajes)

    fig, ax = plt.subplots()
    ax.plot(x_p, y_p, label="Cornisa (función)", color='gray', zorder=1)
    ax.plot(x_a, y_a, 'o-', label="Línea de vida", color='red', zorder=2)
    ax.set_title("Línea de vida sobre función")
    ax.set_aspect('equal')
    ax.grid(True)
    ax.legend()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.pyplot(fig)

    # Descarga CSV
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(["x", "y", "posición"])
    for a, p in zip(anclajes, posiciones):
        csv_writer.writerow([f"{a[0]:.2f}", f"{a[1]:.2f}", f"{p:.2f}"])
    st.download_button("📥 Descargar CSV", csv_buffer.getvalue(), file_name="anclajes.csv", mime="text/csv")

    # Descarga PDF
    pdf_bytes = exportar_pdf(anclajes, posiciones, buf.getvalue())
    st.download_button("📄 Descargar PDF", pdf_bytes, file_name="reporte_linea_vida.pdf", mime="application/pdf")
