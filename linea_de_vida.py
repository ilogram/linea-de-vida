import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from sympy import symbols, lambdify, sympify, diff

# Definir x como variable simbólica
x = symbols('x')

def calcular_distancia(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calcular_longitud_linea_vida(anclajes):
    longitud = 0.0
    for i in range(1, len(anclajes)):
        longitud += calcular_distancia(anclajes[i-1], anclajes[i])
    return longitud

def normal_a_funcion(expr, x_val, distancia):
    # Derivada simbólica de la función con respecto a x
    f_prime = diff(expr, x)
    
    # Evaluamos la derivada en x_val para obtener la pendiente de la tangente
    pendiente_tangente = f_prime.subs(x, x_val)
    
    # Aseguramos que pendiente_tangente sea un número flotante
    pendiente_tangente = float(pendiente_tangente)  # Convertimos a float si es necesario
    
    # La pendiente normal es la opuesta a la tangente (-1/m)
    pendiente_normal = -1 / pendiente_tangente if pendiente_tangente != 0 else float('inf')
    
    # Normalizada a distancia ortogonal (distancia de 0.1m)
    dx = distancia / np.sqrt(1 + pendiente_normal**2)
    dy = pendiente_normal * dx

    return dx, dy

def generar_puntos_funcion(expr, x_min, x_max, distancia_maxima):
    f = lambdify(x, expr, 'numpy')  # Función numérica para evaluación
    expr_sym = sympify(expr)  # Expresión simbólica para diferenciación

    # Genera puntos densos para evaluar distancia real sobre curva
    x_vals = np.linspace(x_min, x_max, 1000)
    y_vals = f(x_vals)
    puntos = list(zip(x_vals, y_vals))

    # Lista para almacenar los puntos de anclajes
    anclajes = [puntos[0]]
    distancia_acumulada = 0.0

    for i in range(1, len(puntos)):
        p1 = puntos[i-1]
        p2 = puntos[i]

        # Aseguramos que la línea de vida esté por encima de la función
        if p2[1] < f(p2[0]):
            p2 = (p2[0], f(p2[0]))  # Ajustamos el punto a la función

        # Ajustamos el punto de anclaje para estar 0.1 metros ortogonalmente hacia fuera
        dx, dy = normal_a_funcion(expr_sym, p2[0], 0.1)  # Desplazamiento ortogonal usando la expresión simbólica
        p2_ajustado = (p2[0] + dx, p2[1] + dy)
        
        d = calcular_distancia(p1, p2_ajustado)
        distancia_acumulada += d

        if distancia_acumulada >= distancia_maxima:
            # Verificamos si la línea entre los puntos actuales corta la cornisa
            if detectar_interseccion(anclajes[-1], p2_ajustado, f):
                # Si corta la cornisa, añadimos más puntos
                x_interp = np.linspace(anclajes[-1][0], p2_ajustado[0], 10)
                y_interp = f(x_interp)
                for xi, yi in zip(x_interp[1:], y_interp[1:]):
                    dx, dy = normal_a_funcion(expr_sym, xi, 0.1)  # Desplazamos ortogonalmente
                    anclajes.append((xi + dx, yi + dy))
            else:
                anclajes.append(p2_ajustado)

            distancia_acumulada = 0.0

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

    except Exception as e:
        st.error(f"Error en el formato de los puntos: {e}")
