import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import io
import pandas as pd
from sympy import symbols, lambdify, sympify
from fpdf import FPDF
import tempfile


def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    for i in range(1, len(anclajes)):
        longitud += calcular_distancia(anclajes[i - 1], anclajes[i])
    return longitud


def calcular_maxima_separacion(p1, p2, f, num_puntos=100):
    x_vals = np.linspace(p1[0], p2[0], num_puntos)
    y_linea = np.linspace(p1[1], p2[1], num_puntos)
    y_funcion = f(x_vals)
    distancias = np.abs(y_linea - y_funcion)
    return np.max(distancias)


def generar_puntos_funcion(expr, x_min, x_max, distancia_maxima, separacion_maxima):
    x = symbols('x')
    f_expr = sympify(expr)
    f = lambdify(x, f_expr, 'numpy')

    x_vals = np.arange(x_min, x_max, distancia_maxima / 10)
    y_vals = f(x_vals)
    puntos = list(zip(x_vals, y_vals))

    anclajes = [puntos[0]]
    i = 0

    while i < len(puntos) - 1:
        for j in range(len(puntos) - 1, i, -1):
            p1, p2 = puntos[i], puntos[j]
            max_sep = calcular_maxima_separacion(p1, p2, f)
            if max_sep <= separacion_maxima:
                anclajes.append(p2)
                i = j
                break
        else:
            i += 1

    longitud_linea_vida = calcular_longitud_linea_vida(anclajes)

    posiciones = [0.0]
    for i in range(1, len(anclajes)):
        posiciones.append(posiciones[-1] + calcular_distancia(anclajes[i - 1], anclajes[i]))

    return list(zip(*puntos)), anclajes, longitud_linea_vida, posiciones


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

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output


# STREAMLIT
st.title("Diseñador de Línea de Vida para Trabajo en Altura")
modo = st.selectbox("Modo de entrada", ["Función"])
distancia_maxima = st.number_input("Distancia mínima entre anclajes (m)", min_value=0.05, value=0.1)
separacion_maxima = st.number_input("Separación máxima de la línea respecto a la cornisa (m)", min_value=0.1, value=0.5)

if modo == "Función":
    expr = st.text_input("Introduce la función (en x)", "sin(x) * 3 + 5")
    x_min = st.number_input("Valor mínimo de x", value=0.0)
    x_max = st.number_input("Valor máximo de x", value=20.0)

    if x_max > x_min:
        puntos, anclajes, longitud_linea_vida, posiciones = generar_puntos_funcion(expr, x_min, x_max, distancia_maxima, separacion_maxima)

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        df_anclajes = pd.DataFrame({
            "x": [a[0] for a in anclajes],
            "y": [a[1] for a in anclajes],
            "posición sobre la línea (m)": posiciones
        })

        st.dataframe(df_anclajes)

        csv = df_anclajes.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar tabla de anclajes como CSV", data=csv, file_name="anclajes.csv", mime="text/csv")

        x_p, y_p = puntos
        x_a, y_a = zip(*anclajes)

        fig, ax = plt.subplots()
        ax.plot(x_p, y_p, label="Cornisa (función)", color='gray')
        ax.plot(x_a, y_a, 'o-', label="Línea de vida", color='red')
        ax.set_title("Línea de vida sobre función")
        ax.set_aspect('equal')
        ax.grid(True)
        ax.legend()

        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        st.download_button("Descargar gráfica como PNG", data=buf.getvalue(), file_name="grafica.png", mime="image/png")

        pdf_bytes = exportar_pdf(anclajes, posiciones, buf.getvalue())
        st.download_button("Descargar reporte completo en PDF", data=pdf_bytes, file_name="reporte_linea_vida.pdf", mime="application/pdf")
