import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import io
import pandas as pd
from sympy import symbols, lambdify, sympify


def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    distancias = [0.0]
    for i in range(1, len(anclajes)):
        d = calcular_distancia(anclajes[i - 1], anclajes[i])
        longitud += d
        distancias.append(longitud)
    return longitud, distancias


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


def generar_puntos_funcion(expr, x_min, x_max, distancia_maxima, max_sep):
    x = symbols('x')
    f_expr = sympify(expr)
    f_lambdified = lambdify(x, f_expr, 'numpy')

    puntos = []
    anclajes = []
    x_actual = x_min

    while x_actual <= x_max:
        y_actual = float(f_lambdified(x_actual)) + 0.1
        puntos.append((x_actual, float(f_lambdified(x_actual))))
        anclajes.append((x_actual, y_actual))
        x_actual += 0.1

    anclajes_filtrados = [anclajes[0]]
    i = 0
    while i < len(anclajes) - 1:
        j = i + 1
        while j < len(anclajes) and calcular_distancia(anclajes[i], anclajes[j]) <= distancia_maxima:
            if segmento_dentro_rango(anclajes[i], anclajes[j], f_lambdified, paso=0.1, max_sep=max_sep):
                j += 1
            else:
                break
        anclajes_filtrados.append(anclajes[j - 1])
        i = j - 1

    longitud_linea_vida, posiciones_lineales = calcular_longitud_linea_vida(anclajes_filtrados)
    return puntos, anclajes_filtrados, longitud_linea_vida, posiciones_lineales


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

    longitud_linea_vida, posiciones_lineales = calcular_longitud_linea_vida(anclajes)
    return anclajes, longitud_linea_vida, posiciones_lineales


# STREAMLIT
st.title("Diseñador de Línea de Vida para Trabajo en Altura")
modo = st.selectbox("Modo de entrada", ["Función", "Lista de puntos"])
distancia_maxima = st.number_input("Distancia máxima entre anclajes (m)", min_value=0.1, value=5.0)
max_sep = st.number_input("Separación máxima permitida respecto a la cornisa (m)", min_value=0.1, value=0.5)

if modo == "Función":
    expr = st.text_input("Introduce la función (en x)", "sin(x) * 3 + 5")
    x_min = st.number_input("Valor mínimo de x", value=0.0)
    x_max = st.number_input("Valor máximo de x", value=20.0)

    if x_max > x_min:
        puntos, anclajes, longitud_linea_vida, posiciones_lineales = generar_puntos_funcion(expr, x_min, x_max, distancia_maxima, max_sep)

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        st.subheader("Coordenadas y ubicación a lo largo de la línea de vida")
        df = pd.DataFrame({
            "Anclaje": [f"A{i+1}" for i in range(len(anclajes))],
            "X": [a[0] for a in anclajes],
            "Y": [a[1] for a in anclajes],
            "Distancia (m)": posiciones_lineales
        })
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar tabla de anclajes (CSV)", csv, "anclajes.csv", "text/csv")

        x_p, y_p = zip(*puntos)
        x_a, y_a = zip(*anclajes)

        fig, ax = plt.subplots()
        ax.plot(x_p, y_p, label="Silueta (función)", color='gray')
        ax.plot(x_a, y_a, 'o-', label="Línea de vida", color='red')
        ax.set_title("Línea de vida sobre función")
        ax.set_aspect('equal')
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        st.download_button("Descargar gráfica (PNG)", buf.getvalue(), "grafica_linea_vida.png", "image/png")

elif modo == "Lista de puntos":
    texto_puntos = st.text_area("Introduce puntos como [(x1, y1), (x2, y2), ...]", "[(0, 0), (5, 2), (9, 2), (12, 6)]")

    try:
        lista_puntos = eval(texto_puntos)
        anclajes, longitud_linea_vida, posiciones_lineales = generar_puntos_desde_lista(lista_puntos, distancia_maxima)

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        st.subheader("Coordenadas y ubicación a lo largo de la línea de vida")
        df = pd.DataFrame({
            "Anclaje": [f"A{i+1}" for i in range(len(anclajes))],
            "X": [a[0] for a in anclajes],
            "Y": [a[1] for a in anclajes],
            "Distancia (m)": posiciones_lineales
        })
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar tabla de anclajes (CSV)", csv, "anclajes.csv", "text/csv")

        x_p, y_p = zip(*lista_puntos)
        x_a, y_a = zip(*anclajes)

        fig, ax = plt.subplots()
        ax.plot(x_p, y_p, '--', label="Silueta (puntos)", color='gray')
        ax.plot(x_a, y_a, 'o-', label="Línea de vida", color='blue')
        ax.set_title("Línea de vida sobre puntos")
        ax.set_aspect('equal')
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        st.download_button("Descargar gráfica (PNG)", buf.getvalue(), "grafica_linea_vida.png", "image/png")

    except Exception as e:
        st.error(f"Error en el formato de los puntos: {e}")
