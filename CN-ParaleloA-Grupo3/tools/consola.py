"""Corre el método en la consola, sin interfaz (para la revisión de avance).

    python tools/consola.py                      # ejemplo del libro
    python tools/consola.py "sin(x)" 0 pi/3 6 3  # f(x), x0, x, orden máximo n, cifras s
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metodo.taylor import calcular_taylor  # noqa: E402
from utilidades import formato_error_pct, formato_valor  # noqa: E402


def main(argv):
    texto_f, x0, x, n, s = (argv + ["cos(x)", "pi/4", "pi/3", "6", "3"][len(argv):])[:5]
    res, _, _ = calcular_taylor(texto_f, x0, x, int(n), int(s))
    print(f"f(x) = {texto_f},  x0 = {res.x0:.6g},  x = {res.x:.6g},  valor verdadero = "
          f"{formato_valor(res.valor_verdadero)}")
    print(f"{'n':>2} {'Pn(x)':>14} {'Et':>14} {'et (%)':>12} {'ea (%)':>12} {'Rn':>14}")
    for f in res.filas:
        marca = "  <-- |ea| < es" if f.n == res.n_cumple else ""
        print(f"{f.n:>2} {formato_valor(f.pn):>14} {formato_valor(f.et):>14} "
              f"{formato_error_pct(f.et_pct):>12} {formato_error_pct(f.ea_pct):>12} "
              f"{formato_valor(f.rn):>14}{marca}")
    if res.terminos_necesarios:
        print(f"es = {res.es_pct:g} %  ->  se cumple con {res.terminos_necesarios} términos")
    else:
        print(f"es = {res.es_pct:g} %  ->  no se cumple con n = {n}")


if __name__ == "__main__":
    main(sys.argv[1:])
