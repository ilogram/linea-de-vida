import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from sympy import symbols, lambdify, sympify, diff, solve

def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    for i in range(1, len(anclajes)):
        longitud += calcular_distancia(anclajes[i-1], anclajes[i])
    return longitud

def normal_a_funcion(f, x_val, distancia_ortogonal):
    x = symbols('x')
    f_prime = diff(f, x)

    # Calculamos la pendiente de la tangente
    m_tangente = f_prime.subs(x, x_val)
    
    # Convertir a tipo float
    m_tangente = float(m_tangente)

    # La pendiente de la normal es el negativo recíproco de la pendiente de la tangente
    m_normal = -1 / m_tangente

    # Calculamos el desplazamiento ortogonal
    dx = distancia_ortogonal / np.sqrt(1 + m_normal ** 2)
    dy = m_normal * dx

    return dx, dy

def detectar_interseccion(p1, p2, f):
    x_vals = np.linspace(p1[0], p2[0], 1000)
    y_vals = f(x_vals)

    for i in range(len(x_vals) - 1):
        if (y_vals[i] < p1[1] and y_vals[i + 1] > p2[1]) or (y_vals[i] > p1[1] and y_vals[i + 1] < p2[1]):
            # Intersección encontrada
            return x_vals[i], y_vals[i]

    return None

def encontrar_puntos_criticos(f):
    # Derivada de la función
    x = symbols('x')
    f_prime = diff(f, x)
    
    # Resolver la derivada igual a cero (puntos críticos)
    soluciones = solve(f_prime, x)
    
    # Filtrar soluciones para que sean números reales
    puntos_criticos = [float(sol.evalf()) for sol in soluciones if sol.is_real]
    
    return puntos_criticos

def generar_puntos_funcion(expr, x_min, x_max, distancia_maxima):
    x = symbols('x')
    f = lambdify(x, sympify(expr), 'numpy')

    # Generar puntos densos para evaluar distancia real sobre la curva
    x_vals = np.linspace(x_min, x_max, 1000)
    y_vals = f(x_vals)
    puntos = list(zip(x_vals, y_vals))

    # Lista para almacenar los puntos de anclajes
    anclajes = [puntos[0]]
    distancia_acumulada = 0.0

    # Encontrar puntos críticos donde la derivada es cero
    puntos_criticos = encontrar_puntos_criticos(sympify(expr))
    
    # Añadir un anclaje en cada punto crítico desplazado ortogonalmente
    for x_crit in puntos_criticos:
        if x_min <= x_crit <= x_max:
            # Encontrar el valor de y en el punto crítico
            y_crit = f(x_crit)
            # Desplazar ortogonalmente el punto
            dx, dy = normal_a_funcion(sympify(expr), x_crit, 0.1)  # Desplazamiento ortogonal
            nuevo_anclaje = (x_crit + dx, y_crit + dy)
            
            # Aseguramos que no se repita un punto ya añadido
            if not any(np.allclose(nuevo_anclaje, anclaje) for anclaje in anclajes):
                anclajes.append(nuevo_anclaje)

    # Añadir puntos intermedios respetando la distancia máxima
    for i in range(1, len(puntos)):
        p1 = anclajes[-1]  # Usamos el último anclaje añadido
        p2 = puntos[i]

        # Aseguramos que la línea de vida esté por encima de la función
        dx, dy = normal_a_funcion(sympify(expr), p2[0], 0.1)  # Desplazamiento ortogonal
        p2_ajustado = (p2[0] + dx, p2[1] + dy)  # Desplazamos el punto ortogonalmente

        d = calcular_distancia(p1, p2_ajustado)
        distancia_acumulada += d

        # Solo añadir el anclaje si la distancia acumulada es mayor o igual a la distancia máxima
        if distancia_acumulada >= distancia_maxima:
            anclajes.append(p2_ajustado)
            distancia_acumulada = 0.0
        else:
            # Si la distancia no es suficiente, no añadimos un nuevo anclaje
            continue

    # Calcular la longitud de la línea de vida
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

    # Calcular la longitud de la línea de vida
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

        # Mostrar la longitud de la línea de vida
        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        # GRAFICAR
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

        # Mostrar la longitud de la línea de vida
        st.write(f"La longitud total de la línea de vida es: {longitud_linea_vida:.2f} metros")

        # GRAFICAR
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
