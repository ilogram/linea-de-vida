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
        p1, p2 = np.array(lista_puntos[i - 1]), np.array(lista_puntos
