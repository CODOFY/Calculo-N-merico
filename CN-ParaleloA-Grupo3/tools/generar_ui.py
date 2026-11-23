"""Convierte ui/ventana_principal.ui en ui_ventana_principal.py con pyside6-uic.

Uso (con el entorno virtual activado, desde la carpeta del proyecto):

    python tools/generar_ui.py

Es lo mismo que:  pyside6-uic ui/ventana_principal.ui -o ui_ventana_principal.py
Hay que repetirlo cada vez que se modifique el diseño en Qt Designer.
El archivo generado NO se edita a mano.
"""
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "ui" / "ventana_principal.ui"
SALIDA = RAIZ / "ui_ventana_principal.py"


def main() -> int:
    uic = shutil.which("pyside6-uic")
    if uic is None:
        print("No se encontró «pyside6-uic». Activa el entorno virtual e instala:\n"
              "    pip install pyside6")
        return 1
    subprocess.run([uic, str(ENTRADA), "-o", str(SALIDA)], check=True)
    print(f"Generado: {SALIDA.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
