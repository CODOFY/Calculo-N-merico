"""Pruebas del programa de Taylor (caso del sensor de nivel y ejemplo del libro).

Ejecutar desde la carpeta del proyecto:  pytest -v

Las pruebas «puras» usan derivadas calculadas a mano (sin SymPy), así que comprueban solo la
lógica numérica. Las que dicen ``sympy`` además prueban la conexión texto -> derivadas y se
omiten si SymPy no está instalado. ``sympy.series`` se usa SOLO aquí, para comparar.
"""
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from metodo.taylor import (  # noqa: E402
    estudio_truncamiento,
    hallar_h_limite,
    tabla_taylor,
    tolerancia_scarborough,
)


# ----- derivadas calculadas a mano ----------------------------------------- #
def derivadas_cos(x0, k_max):
    ciclo = [math.cos(x0), -math.sin(x0), -math.cos(x0), math.sin(x0)]
    return [ciclo[k % 4] for k in range(k_max + 1)]


def derivadas_raiz(x0, k_max, k_const=1.0):
    """Derivadas de k·sqrt(x):  k·(1/2)(−1/2)(−3/2)... · x^(1/2 − k)."""
    valores, coef = [], 1.0
    for k in range(k_max + 1):
        valores.append(k_const * coef * x0 ** (0.5 - k))
        coef *= 0.5 - k
    return valores


# Datos del sensor de nivel: Q = 0.6·sqrt(h), h0 = 2 m, h = 2.5 m
X0, X = 2.0, 2.5
VERDADERO = 0.6 * math.sqrt(X)


def f_sensor(h):
    return 0.6 * math.sqrt(h)


# ----- 1. Sensor de nivel: valores por orden ------------------------------- #
def test_sensor_valor_verdadero_y_ordenes_0_1_2():
    res = tabla_taylor(derivadas_raiz(X0, 6, 0.6), X0, X, VERDADERO, 4, s=3)
    assert VERDADERO == pytest.approx(0.948683298, abs=1e-9)
    assert res.filas[0].pn == pytest.approx(0.848528137, abs=1e-9)
    assert res.filas[0].et_pct == pytest.approx(10.6, abs=0.05)
    assert res.filas[1].pn == pytest.approx(0.954594155, abs=1e-9)
    assert res.filas[1].et_pct == pytest.approx(-0.623, abs=5e-4)
    assert res.filas[2].pn == pytest.approx(0.947965029, abs=1e-9)
    assert res.filas[2].et_pct == pytest.approx(7.57e-2, rel=1e-2)


# ----- 2. Sensor de nivel: criterio de Scarborough ------------------------- #
def test_sensor_scarborough_cinco_terminos():
    res = tabla_taylor(derivadas_raiz(X0, 8, 0.6), X0, X, VERDADERO, 6, s=3)
    assert res.es_pct == pytest.approx(0.05)
    assert res.n_cumple == 4
    assert res.terminos_necesarios == 5
    assert abs(res.filas[3].ea_pct) > 0.05          # n = 3 todavía no cumple
    assert abs(res.filas[4].ea_pct) < 0.05          # n = 4 sí cumple


# ----- 3. Sensor de nivel: hasta dónde sirve cada polinomio ---------------- #
def test_sensor_limite_de_la_recta_tangente():
    derivadas = derivadas_raiz(X0, 4, 0.6)
    h1 = hallar_h_limite(f_sensor, derivadas, X0, 1, tol_pct=1.0, h_max=1.5)
    h2 = hallar_h_limite(f_sensor, derivadas, X0, 2, tol_pct=1.0, h_max=1.5)
    assert h1 == pytest.approx(0.653, abs=0.005)    # recta tangente: error < 1 % hasta h ≈ 0.65 m
    assert h2 > h1                                   # el orden 2 aguanta más lejos


# ----- 4. Estudio del truncamiento: pendiente ≈ n + 1 ---------------------- #
@pytest.mark.parametrize("n", [1, 2, 3])
def test_sensor_pendiente_log_log(n):
    est = estudio_truncamiento(f_sensor, derivadas_raiz(X0, n + 1, 0.6), X0, n, 0.02, 0.4)
    assert est.pendiente == pytest.approx(n + 1, abs=0.3)


# ----- 5. Ejemplo del libro (cap. 4): cos x, x0 = π/4, x = π/3 ------------- #
def test_ejemplo_libro_cos():
    x0, x = math.pi / 4, math.pi / 3
    res = tabla_taylor(derivadas_cos(x0, 7), x0, x, 0.5, 6, s=3)
    esperado = [
        (0.707106781, -41.4),
        (0.521986659, -4.40),
        (0.497754491, 0.449),
        (0.499869147, 2.62e-2),
        (0.500007551, -1.51e-3),
        (0.500000304, -6.08e-5),
        (0.499999988, 2.44e-6),
    ]
    for fila, (pn, et_pct) in zip(res.filas, esperado):
        assert fila.pn == pytest.approx(pn, abs=1e-9)
        assert fila.et_pct == pytest.approx(et_pct, rel=2e-2)


# ----- 6. Ejemplo del libro: e^0.5 por Maclaurin con 3 cifras -------------- #
def test_scarborough_exp_maclaurin():
    assert tolerancia_scarborough(3) == pytest.approx(0.05)
    res = tabla_taylor([1.0] * 12, 0.0, 0.5, math.exp(0.5), 8, s=3)
    assert res.terminos_necesarios == 6
    fila = res.filas[res.n_cumple]
    assert fila.pn == pytest.approx(1.648697917, abs=1e-9)
    assert fila.et_pct == pytest.approx(1.42e-3, rel=1e-2)


# ----- 7. El residuo estimado es del orden del error verdadero ------------- #
def test_residuo_estimado_cercano_al_error_verdadero():
    res = tabla_taylor(derivadas_raiz(X0, 8, 0.6), X0, X, VERDADERO, 5, s=3)
    for fila in res.filas[1:]:
        assert abs(fila.rn) == pytest.approx(abs(fila.et), rel=0.5)


# ----- Con SymPy: texto -> derivadas -> tabla ------------------------------ #
def test_sympy_sensor_de_nivel_desde_texto():
    pytest.importorskip("sympy")
    from metodo.taylor import calcular_taylor

    res, f, _ = calcular_taylor("0.6*sqrt(x)", "2", "2.5", 4, 3)
    assert f(2.5) == pytest.approx(0.948683298, abs=1e-9)
    assert res.filas[0].pn == pytest.approx(0.848528137, abs=1e-9)
    assert res.filas[1].pn == pytest.approx(0.954594155, abs=1e-9)
    assert res.filas[2].pn == pytest.approx(0.947965029, abs=1e-9)
    assert res.terminos_necesarios == 5


def test_sympy_ejemplo_libro_desde_texto():
    pytest.importorskip("sympy")
    from metodo.taylor import calcular_taylor

    res, f, _ = calcular_taylor("cos(x)", "pi/4", "pi/3", 6, 3)
    assert f(math.pi / 3) == pytest.approx(0.5)
    assert res.filas[3].pn == pytest.approx(0.499869147, abs=1e-9)


def test_sympy_texto_invalido_lanza_error():
    pytest.importorskip("sympy")
    from metodo.expresiones import ErrorExpresion
    from metodo.taylor import calcular_taylor

    for malo in ["", "cos(", "x +* 2", "y + x"]:
        with pytest.raises(ErrorExpresion):
            calcular_taylor(malo, "0", "1", 3, 3)


def test_sympy_series_como_referencia():
    sp = pytest.importorskip("sympy")
    from metodo.taylor import calcular_taylor

    x = sp.Symbol("x")
    serie = sp.series(sp.Rational(3, 5) * sp.sqrt(x), x, 2, 3).removeO()   # solo para comparar
    res, _, _ = calcular_taylor("0.6*sqrt(x)", "2", "2.5", 2, 3)
    assert res.filas[2].pn == pytest.approx(float(serie.subs(x, 2.5)), abs=1e-9)


# ----- Consistencia del archivo .ui con main.py (sin necesitar Qt) --------- #
def test_ui_tiene_todos_los_controles_que_usa_main():
    ui = ET.parse(os.path.join(RAIZ, "ui", "ventana_principal.ui")).getroot()
    nombres = [w.get("name") for w in ui.iter() if w.tag in ("widget", "layout") and w.get("name")]
    assert len(nombres) == len(set(nombres)), "objectName repetido en el .ui"
    with open(os.path.join(RAIZ, "main.py"), encoding="utf-8") as fh:
        usados = set(re.findall(r"self\.ui\.(\w+)", fh.read()))
    usados -= {"setupUi", "retranslateUi"}
    faltan = usados - set(nombres)
    assert not faltan, f"main.py usa controles que no existen en el .ui: {faltan}"
