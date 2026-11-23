"""Proyecto A: serie de Taylor y error de truncamiento (solo lógica numérica).

Este archivo no importa nada de Qt, así que se puede probar con ``pytest``.

Fórmulas (Chapra y Canale, cap. 4)::

    P_n(x) = sum_{k=0}^{n} f^(k)(x0) / k! * h^k          con h = x - x0
    R_n   ~= f^(n+1)(x0) / (n+1)! * h^(n+1)               (residuo estimado)
    et    = (v_verdadero - v_aprox) / v_verdadero * 100   (error relativo verdadero, %)
    ea    = (P_n - P_{n-1}) / P_n * 100                   (error relativo aproximado, %)
    es    = 0.5 * 10^(2 - s)  %                           (criterio de Scarborough)

Todo se calcula a mano: la única ayuda externa son las derivadas f^(k)(x0), que
llegan como una lista de números (``derivadas``). ``calcular_taylor`` las obtiene
con SymPy; las pruebas también pueden darlas directamente.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

import numpy as np

NAN = float("nan")


# --------------------------------------------------------------------------- #
#  Estructuras de resultados
# --------------------------------------------------------------------------- #
@dataclass
class FilaTaylor:
    """Una fila de la tabla: resultados al sumar hasta el orden ``n``."""

    n: int
    termino: float          # término agregado: f^(n)(x0)/n! * h^n
    pn: float               # aproximación P_n(x)
    et: float               # error verdadero Et = v_verdadero - P_n
    et_pct: float           # error relativo verdadero (%)
    ea_pct: float           # error relativo aproximado (%); nan para n = 0
    rn: float               # residuo estimado R_n (primer término omitido)


@dataclass
class ResultadoTaylor:
    x0: float
    x: float
    h: float
    valor_verdadero: float
    s: int                              # cifras significativas pedidas
    es_pct: float                       # tolerancia de Scarborough (%)
    derivadas: List[float]
    filas: List[FilaTaylor]
    n_cumple: Optional[int] = None      # primer orden con |ea| < es (None si no se cumple)

    @property
    def terminos_necesarios(self) -> Optional[int]:
        """Número de términos (no de orden): orden + 1."""
        return None if self.n_cumple is None else self.n_cumple + 1


@dataclass
class EstudioTruncamiento:
    """Datos para la gráfica log-log |Et| vs h de un orden fijo."""

    n: int
    h: np.ndarray
    error_abs: np.ndarray               # |Et| para cada h
    usados: np.ndarray                  # máscara: puntos usados en el ajuste
    pendiente: float                    # pendiente de log|Et| vs log h (≈ n + 1)
    ordenada: float                     # log10 de la constante C en |Et| ≈ C·h^p


# --------------------------------------------------------------------------- #
#  Funciones básicas
# --------------------------------------------------------------------------- #
def tolerancia_scarborough(s: int) -> float:
    """εs = 0.5 × 10^(2 − s) %  (s = cifras significativas)."""
    return 0.5 * 10.0 ** (2 - s)


def polinomio_taylor(derivadas: Sequence[float], x0: float, x, n: int):
    """Evalúa P_n(x) sumando los términos uno a uno.

    ``x`` puede ser un número o un arreglo de NumPy (se usa para graficar).
    """
    h = np.asarray(x, dtype=float) - x0
    suma = np.zeros_like(h)
    potencia = np.ones_like(h)       # h^k
    factorial = 1.0                  # k!
    for k in range(n + 1):
        if k > 0:
            potencia = potencia * h
            factorial *= k
        suma = suma + derivadas[k] / factorial * potencia
    return suma


def tabla_taylor(
    derivadas: Sequence[float],
    x0: float,
    x: float,
    valor_verdadero: float,
    n_max: int,
    s: int,
) -> ResultadoTaylor:
    """Construye la tabla de órdenes 0..n_max.

    ``derivadas`` debe traer f^(k)(x0) para k = 0..n_max+1 (la última sirve
    para estimar el residuo del último orden).
    """
    if n_max < 0:
        raise ValueError("El orden máximo n debe ser mayor o igual que 0.")
    if len(derivadas) < n_max + 2:
        raise ValueError("Se necesitan las derivadas de orden 0 hasta n_max + 1.")

    h = x - x0
    es = tolerancia_scarborough(s)
    filas: List[FilaTaylor] = []
    n_cumple: Optional[int] = None

    suma = 0.0
    potencia = 1.0       # h^n
    factorial = 1.0      # n!
    pn_anterior: Optional[float] = None

    for n in range(n_max + 1):
        if n > 0:
            potencia *= h
            factorial *= n
        termino = derivadas[n] * potencia / factorial
        suma += termino

        # Residuo estimado: primer término que se deja fuera, f^(n+1)(x0)/(n+1)! h^(n+1)
        residuo = derivadas[n + 1] * potencia * h / (factorial * (n + 1))

        et = valor_verdadero - suma
        et_pct = et / valor_verdadero * 100.0 if valor_verdadero != 0 else NAN
        if pn_anterior is None or suma == 0:
            ea_pct = NAN
        else:
            ea_pct = (suma - pn_anterior) / suma * 100.0

        # Un término nulo (p. ej. orden par de sen x en x0 = 0) hace ea = 0 sin que la
        # serie haya convergido: esa fila no puede cumplir el criterio de parada.
        referencia = max(abs(suma), abs(valor_verdadero), 1e-300)
        aporta = abs(termino) > 1e-13 * referencia
        if n_cumple is None and aporta and not math.isnan(ea_pct) and abs(ea_pct) < es:
            n_cumple = n

        filas.append(FilaTaylor(n, termino, suma, et, et_pct, ea_pct, residuo))
        pn_anterior = suma

    return ResultadoTaylor(
        x0=x0,
        x=x,
        h=h,
        valor_verdadero=valor_verdadero,
        s=s,
        es_pct=es,
        derivadas=list(derivadas),
        filas=filas,
        n_cumple=n_cumple,
    )


# --------------------------------------------------------------------------- #
#  Estudio del truncamiento: |Et| vs h en escala log-log
# --------------------------------------------------------------------------- #
def estudio_truncamiento(
    f: Callable[[float], float],
    derivadas: Sequence[float],
    x0: float,
    n: int,
    h_min: float,
    h_max: float,
    puntos: int = 30,
) -> EstudioTruncamiento:
    """Calcula |Et| para ``puntos`` valores de h entre ``h_min`` y ``h_max``.

    Con h pequeño |Et| ≈ C·h^(n+1), así que en escala log-log es una recta de
    pendiente n+1. Los puntos con |Et| cercano al error de redondeo (~1e-13)
    no se usan en el ajuste porque ahí domina el redondeo, no el truncamiento.
    """
    if not (0 < h_min < h_max):
        raise ValueError("Se requiere 0 < h_min < h_max.")
    if len(derivadas) < n + 1:
        raise ValueError("Faltan derivadas para el orden pedido.")

    h = np.geomspace(h_min, h_max, puntos)
    error = np.empty(puntos)
    for i, hi in enumerate(h):
        verdadero = f(x0 + hi)
        aprox = float(polinomio_taylor(derivadas, x0, x0 + hi, n))
        error[i] = abs(verdadero - aprox)

    escala = max(abs(f(x0)), 1.0)
    usados = np.isfinite(error) & (error > 1e-12 * escala)
    if usados.sum() < 3:
        return EstudioTruncamiento(n, h, error, usados, NAN, NAN)

    lx = np.log10(h[usados])
    ly = np.log10(error[usados])
    # Mínimos cuadrados de ly = m·lx + b, escritos a mano.
    mx, my = lx.mean(), ly.mean()
    m = float(np.sum((lx - mx) * (ly - my)) / np.sum((lx - mx) ** 2))
    b = float(my - m * mx)
    return EstudioTruncamiento(n, h, error, usados, m, b)


# --------------------------------------------------------------------------- #
#  Hasta qué h el polinomio de orden n tiene error menor que una tolerancia
# --------------------------------------------------------------------------- #
def hallar_h_limite(
    f: Callable[[float], float],
    derivadas: Sequence[float],
    x0: float,
    n: int,
    tol_pct: float,
    h_max: float,
    pasos: int = 400,
) -> Optional[float]:
    """Mayor h > 0 tal que |εt| < ``tol_pct`` % para todo h' menor que h.

    Recorre h desde 0 hasta ``h_max`` y, al detectar el primer cruce de la
    tolerancia, afina con bisección. Devuelve ``None`` si en [0, h_max] el error
    nunca supera la tolerancia.
    """

    def error_pct(h: float) -> float:
        verdadero = f(x0 + h)
        aprox = float(polinomio_taylor(derivadas, x0, x0 + h, n))
        if verdadero == 0:
            return NAN
        return abs((verdadero - aprox) / verdadero) * 100.0

    a = 0.0                              # último h que todavía cumple la tolerancia
    for i in range(1, pasos + 1):
        b = h_max * i / pasos
        e = error_pct(b)
        if not math.isnan(e) and e >= tol_pct:
            for _ in range(60):          # bisección sobre g(h) = error(h) - tol
                m = 0.5 * (a + b)
                em = error_pct(m)
                if math.isnan(em) or em < tol_pct:
                    a = m
                else:
                    b = m
            return 0.5 * (a + b)
        a = b
    return None


# --------------------------------------------------------------------------- #
#  Conexión con SymPy (texto -> derivadas)
# --------------------------------------------------------------------------- #
def calcular_taylor(
    texto_f: str,
    texto_x0: str,
    texto_x: str,
    n_max: int,
    s: int,
    n_derivadas: Optional[int] = None,
):
    """Lee las entradas de texto, deriva con SymPy y arma la tabla.

    ``n_derivadas`` permite pedir más derivadas que las de la tabla (la ventana
    las necesita para el estudio de truncamiento con otro orden).

    Devuelve ``(resultado, f_escalar, f_vectorial)``. Lanza ``ErrorExpresion``
    (subclase de ``ValueError``) si algún texto no es válido.
    """
    from . import expresiones as ex   # import tardío: SymPy solo se necesita aquí

    expr = ex.parsear_funcion(texto_f)
    x0 = ex.evaluar_constante(texto_x0)
    x = ex.evaluar_constante(texto_x)
    f_escalar, f_vectorial = ex.a_callables(expr)

    derivadas = ex.derivadas_en_punto(expr, x0, max(n_max + 1, n_derivadas or 0))
    valor_verdadero = f_escalar(x)
    if not math.isfinite(valor_verdadero):
        raise ex.ErrorExpresion(f"La función no está definida en x = {x:g}.")

    resultado = tabla_taylor(derivadas, x0, x, valor_verdadero, n_max, s)
    return resultado, f_escalar, f_vectorial
