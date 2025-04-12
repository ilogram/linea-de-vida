import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import re
from sympy import symbols, lambdify, sympify
from math import sqrt

st.set_page_config(page_title="Diseñador de Línea de Vida", layout="centered")

st.title("🧗 Diseñador de Línea de Vida en Trabajos en Altura")

st.markdown("Introduce la **forma de la superficie** por una función matemática o puntos, y obtendrás los anclajes necesarios.")

# Entrada del tipo de definición
input_method = st.radio("¿Cómo quieres definir la superficie?", ["Fórmula matemática", "Lista de puntos"])

points = []

if input_method == "Fórmula matemática":
    expr_str = st.text_input("Introduce la función (por ejemplo: sin(x) o x**2):", value="sin(x)")
    rango = st.slider("Selecciona el rango de x", -20, 20, (-5, 5))
    densidad = st.slider("Densidad de puntos para graficar", 10, 500, 100)

    if expr_str:
        x = symbols('x')
        try:
            expr = sympify(expr_str)
            func = lambdify(x, expr, modules=["numpy"])
            x_vals = np.linspace(rango[0], rango[1], densidad)
            y_vals = func(x_vals)

            points = list(zip(x_vals, y_vals))
        except Exception as e:
            st.error(f"Error al interpretar la función: {e}")

elif input_method == "Lista de puntos":
    texto = st.text_area("Introduce los puntos como (x,y), separados por coma:", value="(0,0), (3,0), (3,4), (0,4)")
    matches = re.findall(r"\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?", texto)
    try:
        points = [(float(x), float(y)) for x, y in matches]
    except:
        st.error("Revisa el formato. Debe ser como: (0,0), (3,0), (3,4)")

# Parámetros técnicos
if points:
    st.subheader("Parámetros técnicos")
    max_dist = st.number_input("Distancia máxima entre anclajes (en metros):", value=5.0, min_value=1.0)

    # Calcular longitud y anclajes
    total_length = 0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        total_length += sqrt(dx**2 + dy**2)

    num_anchors = int(np.ceil(total_length / max_dist)) + 1

    st.markdown(f"**Longitud total:** {total_length:.2f} m")
    st.markdown(f"**Número recomendado de anclajes:** {num_anchors}")

    # Crear anclajes distribuidos
    def distribuir_anclajes(puntos, max_distancia):
        anclajes = [puntos[0]]
        distancia_actual = 0
        for i in range(1, len(puntos)):
            p1 = puntos[i-1]
            p2 = puntos[i]
            segmento = sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
            distancia_actual += segmento
            if distancia_actual >= max_distancia:
                anclajes.append(p2)
                distancia_actual = 0
        if anclajes[-1] != puntos[-1]:
            anclajes.append(puntos[-1])
        return anclajes

    anclajes = distribuir_anclajes(points, max_dist)

    # Graficar
    st.subheader("Visualización de la línea y anclajes")
    fig, ax = plt.subplots()
    xs, ys = zip(*points)
    ax.plot(xs, ys, label="Recorrido superficie", color="blue")

    ax.scatter(*zip(*anclajes), color="red", zorder=5, label="Anclajes")

    for i, (x, y) in enumerate(anclajes):
        ax.annotate(f"A{i+1}", (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)

    ax.set_aspect('equal')
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
