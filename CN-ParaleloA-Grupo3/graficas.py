"""Funciones de Matplotlib del Proyecto A (reciben un ``Figure``; no usan Qt).

La ventana les pasa el ``Figure`` que está dentro de cada pestaña; en las
pruebas o scripts se les puede pasar cualquier ``Figure``.
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np

from metodo.taylor import EstudioTruncamiento, ResultadoTaylor, polinomio_taylor


def _ejes_vacios(fig, titulo: str):
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_title(titulo)
    ax.grid(True, alpha=0.3)
    return ax


def limpiar(fig, mensaje: str = "Presiona «Calcular»") -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, mensaje, ha="center", va="center", color="gray", transform=ax.transAxes)
    ax.set_axis_off()


def graficar_aproximacion(
    fig,
    f_vectorial: Callable[[np.ndarray], np.ndarray],
    res: ResultadoTaylor,
    unidad_x: str = "",
) -> None:
    """f(x) y los polinomios P0..Pn alrededor de x0, marcando x0 y x."""
    ax = _ejes_vacios(fig, "f(x) y polinomios de Taylor P₀ … Pₙ")
    x0, x, h = res.x0, res.x, res.h
    semiancho = max(1.6 * abs(h), 0.5)
    xs = np.linspace(x0 - semiancho, x0 + semiancho, 600)
    ys = f_vectorial(xs)

    # Límites verticales según f (los polinomios de orden alto se disparan lejos de x0).
    visibles = ys[np.isfinite(ys)]
    if visibles.size:
        ymin, ymax = float(visibles.min()), float(visibles.max())
        pad = max(ymax - ymin, 1e-9)
        ax.set_ylim(ymin - 0.6 * pad, ymax + 0.6 * pad)

    n_max = len(res.filas) - 1
    colores = _paleta(n_max + 1)
    for n in range(n_max + 1):
        yp = polinomio_taylor(res.derivadas, x0, xs, n)
        ax.plot(xs, yp, lw=1.1, color=colores[n], alpha=0.9, label=f"P{n}")
    ax.plot(xs, ys, "k", lw=2.4, label="f(x)")

    ax.axvline(x0, color="tab:blue", ls="--", lw=1)
    ax.axvline(x, color="tab:red", ls="--", lw=1)
    ax.plot([x0], [float(f_vectorial(np.array([x0]))[0])], "o", color="tab:blue", label="x₀")
    ax.plot([x], [res.valor_verdadero], "o", color="tab:red", label="x (a evaluar)")
    etiqueta_x = f" ({unidad_x})" if unidad_x else ""
    ax.set_xlabel("x" + etiqueta_x)
    ax.set_ylabel("f(x)")
    ncol = 2 if n_max > 6 else 1
    ax.legend(fontsize=7, ncol=ncol, loc="best")


def _paleta(k: int):
    """k colores distintos (de azul a rojo) para los polinomios."""
    import matplotlib

    cmap = matplotlib.colormaps["viridis"]
    return [cmap(i / max(k - 1, 1)) for i in range(k)]


def graficar_error_vs_orden(fig, res: ResultadoTaylor) -> None:
    """|εt| contra el orden n en escala semilogarítmica."""
    ax = _ejes_vacios(fig, "Error relativo verdadero |εt| vs. orden n")
    ns = [f.n for f in res.filas if f.et_pct != 0 and math.isfinite(f.et_pct)]
    ys = [abs(f.et_pct) for f in res.filas if f.et_pct != 0 and math.isfinite(f.et_pct)]
    if not ns:
        ax.text(0.5, 0.5, "No hay valores de |εt| > 0 para graficar",
                ha="center", va="center", transform=ax.transAxes)
        return
    ax.semilogy(ns, ys, "o-", color="tab:red", label="|εt| (%)")
    ax.axhline(res.es_pct, color="tab:green", ls="--", label=f"εs = {res.es_pct:g} %")
    if res.n_cumple is not None:
        ax.axvline(res.n_cumple, color="tab:green", ls=":", alpha=0.8)
        ax.annotate(f"|εa| < εs\n({res.terminos_necesarios} términos)",
                    (res.n_cumple, res.es_pct), textcoords="offset points",
                    xytext=(8, 14), fontsize=8, color="tab:green")
    ax.set_xlabel("Orden n")
    ax.set_ylabel("|εt| (%)")
    ax.set_xticks(range(0, len(res.filas)))
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)


def graficar_truncamiento(fig, est: EstudioTruncamiento) -> None:
    """|Et| vs h en escala log-log y recta ajustada (pendiente ≈ n + 1)."""
    ax = _ejes_vacios(fig, f"Truncamiento con orden n = {est.n}:  |Et| vs. h (log-log)")
    validos = est.error_abs > 0
    ax.loglog(est.h[validos & est.usados], est.error_abs[validos & est.usados], "o",
              color="tab:blue", label="|Et| (truncamiento)")
    descartados = validos & ~est.usados
    if descartados.any():
        ax.loglog(est.h[descartados], est.error_abs[descartados], "x", color="tab:gray",
                  label="dominado por redondeo (no se usa)")
    if math.isfinite(est.pendiente):
        hh = np.array([est.h.min(), est.h.max()])
        ax.loglog(hh, 10 ** est.ordenada * hh ** est.pendiente, "-", color="tab:red",
                  label=f"ajuste: pendiente = {est.pendiente:.3f}")
        # Recta de referencia con pendiente exacta n+1, anclada en el último punto usado.
        h_ref = est.h[est.usados][-1]
        e_ref = est.error_abs[est.usados][-1]
        ax.loglog(hh, e_ref * (hh / h_ref) ** (est.n + 1), "--", color="tab:green",
                  label=f"referencia O(h^{est.n + 1}): pendiente {est.n + 1}")
    ax.set_xlabel("h = x − x₀")
    ax.set_ylabel("|Et|")
    ax.legend(fontsize=8)
    ax.grid(True, which="both", alpha=0.3)
