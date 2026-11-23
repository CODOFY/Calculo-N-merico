"""Lectura de funciones escritas como texto, con SymPy.

Este módulo NO contiene código de interfaz. Convierte el texto que escribe el
usuario (por ejemplo ``exp(-x) - x`` o ``pi/4``) en:

* una expresión simbólica de SymPy (para derivar con ``sympy.diff``), y
* funciones numéricas de NumPy (con ``sympy.lambdify``) para evaluar rápido.

Si el texto no es válido se lanza ``ErrorExpresion``; la interfaz la captura y
muestra un ``QMessageBox`` sin cerrar el programa.
"""
from __future__ import annotations

import math
from typing import Callable, List, Tuple

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class ErrorExpresion(ValueError):
    """El texto escrito por el usuario no es una expresión válida."""


# Variable independiente de todas las funciones del proyecto.
X = sp.Symbol("x")

# Nombres que el usuario puede escribir además de los de SymPy (exp, sin, cos...).
_NOMBRES = {
    "x": X,
    "pi": sp.pi,
    "e": sp.E,
    "E": sp.E,
    "sen": sp.sin,
    "tg": sp.tan,
    "ln": sp.log,
    "raiz": sp.sqrt,
    "arcsen": sp.asin,
    "arccos": sp.acos,
    "arctan": sp.atan,
}

# "2x" -> 2*x, "x^2" -> x**2
_TRANSFORMACIONES = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _normalizar(texto: str) -> str:
    texto = (texto or "").strip()
    if not texto:
        raise ErrorExpresion("El campo está vacío. Escribe una expresión, por ejemplo: cos(x)")
    # Aceptar coma decimal (0,5) como si fuera punto.
    return texto.replace(",", ".")


def _parsear(texto: str) -> sp.Basic:
    texto = _normalizar(texto)
    try:
        expr = parse_expr(texto, local_dict=dict(_NOMBRES), transformations=_TRANSFORMACIONES)
    except Exception as exc:  # SyntaxError, TokenError, TypeError, ...
        raise ErrorExpresion(f"No se pudo interpretar «{texto}».\nDetalle: {exc}") from exc
    if not isinstance(expr, sp.Basic):
        raise ErrorExpresion(f"«{texto}» no es una expresión matemática válida.")
    return expr


def parsear_funcion(texto: str) -> sp.Basic:
    """Convierte ``texto`` en una expresión SymPy que depende solo de ``x``."""
    expr = _parsear(texto)
    desconocidos = expr.free_symbols - {X}
    if desconocidos:
        nombres = ", ".join(sorted(str(s) for s in desconocidos))
        raise ErrorExpresion(
            f"La función solo puede depender de x. Símbolos no reconocidos: {nombres}."
        )
    return expr


def evaluar_constante(texto: str) -> float:
    """Evalúa un número escrito como texto; admite ``pi/4``, ``sqrt(2)``, ``1e-3``..."""
    expr = _parsear(texto)
    if expr.free_symbols:
        raise ErrorExpresion(
            f"«{texto}» debe ser un número (puede usar pi, e, sqrt(...)), sin la variable x."
        )
    try:
        valor = float(expr.evalf())
    except (TypeError, ValueError) as exc:
        raise ErrorExpresion(f"«{texto}» no se pudo convertir a un número real.") from exc
    if not math.isfinite(valor):
        raise ErrorExpresion(f"«{texto}» no es un número finito.")
    return valor


def a_callables(expr: sp.Basic) -> Tuple[Callable[[float], float], Callable[[np.ndarray], np.ndarray]]:
    """Devuelve ``(f_escalar, f_vectorial)`` construidas con ``sympy.lambdify``.

    * ``f_escalar(v)``  -> ``float`` (``nan`` si f no está definida en ``v``).
    * ``f_vectorial(xs)`` -> arreglo NumPy del mismo tamaño que ``xs``.
    """
    f_np = sp.lambdify(X, expr, modules="numpy")

    def f_escalar(v: float) -> float:
        with np.errstate(all="ignore"):
            r = f_np(float(v))
        if np.iscomplexobj(r):
            return float("nan")
        return float(r)

    def f_vectorial(xs) -> np.ndarray:
        xs = np.asarray(xs, dtype=float)
        with np.errstate(all="ignore"):
            y = np.asarray(f_np(xs))
        if np.iscomplexobj(y):
            y = np.where(np.abs(y.imag) < 1e-12, y.real, np.nan)
        return np.array(np.broadcast_to(y, xs.shape), dtype=float)

    return f_escalar, f_vectorial


def derivadas_en_punto(expr: sp.Basic, x0: float, k_max: int) -> List[float]:
    """Calcula ``[f(x0), f'(x0), ..., f^(k_max)(x0)]``.

    Las derivadas se obtienen con ``sympy.diff`` y se evalúan con
    ``sympy.lambdify``. Es lo único que se delega a SymPy: la suma de los
    términos de Taylor se programa a mano en ``taylor.py``.
    """
    valores: List[float] = []
    derivada = expr
    for k in range(k_max + 1):
        if k > 0:
            derivada = sp.diff(derivada, X)
        f_k = sp.lambdify(X, derivada, modules="numpy")
        try:
            with np.errstate(all="ignore"):
                v = f_k(float(x0))
            if np.iscomplexobj(v):
                raise ValueError("resultado complejo")
            v = float(v)
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise ErrorExpresion(
                f"La derivada de orden {k} no se puede evaluar en x0 = {x0:g}."
            ) from exc
        if not math.isfinite(v):
            raise ErrorExpresion(
                f"La derivada de orden {k} no es finita en x0 = {x0:g}; "
                "la serie de Taylor no existe en ese punto."
            )
        valores.append(v)
    return valores
