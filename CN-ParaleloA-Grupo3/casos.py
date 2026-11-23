"""Ejemplos precargados del selector (ComboBox): el ejemplo del libro y el caso del sensor de nivel.

Cada caso es un diccionario con los valores que se copian a los controles de la ventana.
"""

CASOS = [
    {
        "nombre": "Ejemplo del libro (cap. 4): cos x, x₀ = π/4, x = π/3",
        "funcion": "cos(x)",
        "x0": "pi/4",
        "x": "pi/3",
        "n": 6,
        "s": 3,
        "n_estudio": 2,
        "h_max": 0.5,
        "tol_limite": 1.0,
        "unidad": "",
        "unidad_x": "",
        "interpretacion": (
            "Ejemplo del libro de Chapra y Canale: se aproxima cos(π/3) = 0.5 usando la "
            "serie de Taylor alrededor de π/4. Cada orden extra reduce el error verdadero "
            "alrededor de un orden de magnitud, hasta llegar al error de redondeo."
        ),
    },
    {
        "nombre": "Sensor de nivel: Q = 0.6·√h alrededor de h₀ = 2 m",
        "funcion": "0.6*sqrt(x)",
        "x0": "2",
        "x": "2.5",
        "n": 4,
        "s": 3,
        "n_estudio": 2,
        "h_max": 1.5,
        "tol_limite": 1.0,
        "unidad": "m³/s",
        "unidad_x": "m",
        "interpretacion": (
            "Linealización de un sensor de nivel: la recta tangente (orden 1) en h₀ = 2 m "
            "es una buena aproximación cerca del punto de operación (error ≈ 0.6 % en "
            "h = 2.5 m); el orden 2 lo baja a ≈ 0.08 %. Lejos de h₀ la recta se separa "
            "de la curva √h y el error crece."
        ),
    },
]

# Índice del caso que se carga al abrir la ventana (el sensor de nivel).
CASO_INICIAL = 1
