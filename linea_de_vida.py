import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from sympy import symbols, lambdify, sympify, diff


def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    for i in range(1, len(anclajes)):
        longitud += calcular_distancia(anclajes[i - 1], anclajes[i])
    return longitud


def normal_a_funcion(f_expr, x_val, distancia_max_ortogonal):
    x = symbols('x')
    f_prime = diff(f_expr, x)
    try:
        m_tangente = float(f_prime.subs(x, x_val))
        m_normal = -1 / m_tangente if abs(m_tangente) > 1e-3 else 0
    except:
        m_normal = 0

    if m_normal == 0:
        return (x_val, float(sympify(f_expr).subs(x, x_val)) + distancia_max_ortogonal)

    dx = distancia_max_ortogonal / np.sqrt(1 + m_normal ** 2)
    dy = m_normal * dx

    x_pos = x_val + dx
    y_pos = float(sympify(f_expr).subs(x, x_val)) + dy

    x_neg = x_val - dx
    y_neg = float(sympify(f_expr).subs(x, x_val)) - dy

    # Elegir el que esté por encima
    return (x_pos, y_pos) if y_pos > y_neg else (x_neg, y_neg)


def detectar_interseccion(p1, p2, f):
    x_vals = np.linspace(min(p1[0], p2[0]), max(p1[0], p2[0]), 500)
    y_vals_func = f(x_vals)

    for x_val, y_func in zip(x_vals, y_vals_func):
        y_seg = p1[1] + (p2[1] - p1[1]) * (x_val - p1[0]) / (p2[0] - p1[0] + 1e-9)
        if y_func > y_seg:
            return True
    return False


def generar_puntos_funcion(expr, x_min, x_max, distancia_maxima):
    x = symbols('x')
    f_expr = sympify(expr)
    f = lambdify(x, f_expr, 'numpy')
    
    anclajes = []
    x_actual = x_min
    p_actual = normal_a_funcion(f_expr, x_actual, 0.1)
    anclajes.append(p_actual)

    while x_actual < x_max:
        x_candidato = x_actual + distancia_maxima
        if x_candidato > x_max:
            x_candidato = x_max

        # Buscar el mejor punto desplazado con restricción de máxima separación vertical
        for d_ort in np.linspace(0.1, 0.5, 10):
            p_candidato = normal_a_funcion(f_expr, x_candidato, d_ort)
            distancia_vertical = abs(p_candidato[1] - float(sympify(f_expr).subs(x, x_candidato)))
            if distancia_vertical <= 0.5 and not detectar_interseccion(p_actual, p_candidato, f):
                anclajes.append(p_candidato)
                x_actual = x_candidato
                p_actual = p_candidato
                break
        else:
            # Si no se encuentra punto seguro, retroceder
            for delta in np.linspace(distancia_maxima, 0.1, 50):
                x_candidato = x_actual + delta
                for d_ort in np.linspace(0.1, 0.5, 10):
                    p_candidato = normal_a_funcion(f_expr, x_candidato, d_ort)
                    distancia_vertical = abs(p_candidato[1] - float(sympify(f_expr).subs(x, x_candidato)))
                    if distancia_vertical <= 0.5 and not detectar_interseccion(p_actual, p_candidato, f):
                        anclajes.append(p_candidato)
                        x_actual = x_candidato
                        p_actual = p_candidato
                        break
                else:
                    continue
                break
            else:
                x_actual += 0.1

    x_vals = np.linspace(x_min, x_max, 1000)
    y_vals = f(x_vals)
    puntos = list(zip(x_vals, y_vals))
    longitud_linea_vida = calcular_longitud_linea_vida(anclajes)
    return puntos, anclajes, longitud_linea_vida


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


# STREAMLIT
st.title("Diseñador de Línea de Vida para Trabajo en Altura")
modo = st.selectbox("Modo de entrada", ["Función", "Lista de puntos"])
distancia_maxima = st.number_input("Distancia máxima entre anclajes (m)", min_value=0.1, value=5.0)

if modo == "Función":
    expr = st.text_input("Introduce la función (en x)", "sin(x) * 3 + 5")
    x_min = st.number_input("Valor mínimo de x", value=0.0)
    x_max = st.number_input("Valor máximo de x", value=20.0)

    if x_max > x_min:
        puntos, anclajes, longitud_linea_vida = generar_puntos_funcion(expr, x_min, x_max, distancia_maxima)

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

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

elif modo == "Lista de puntos":
    texto_puntos = st.text_area("Introduce puntos como [(x1, y1), (x2, y2), ...]", "[(0, 0), (5, 2), (9, 2), (12, 6)]")

    try:
        lista_puntos = eval(texto_puntos)
        anclajes, longitud_linea_vida = generar_puntos_desde_lista(lista_puntos, distancia_maxima)

        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

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

    except Exception as e:
        st.error(f"Error en el formato de los puntos: {e}")
