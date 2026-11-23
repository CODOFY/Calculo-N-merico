"""Punto de entrada del Proyecto A: serie de Taylor y error de truncamiento.

Ejecutar:  python main.py

Capas del proyecto
------------------
* ``ui/ventana_principal.ui``  -> diseño visual (Qt Designer).
* ``ui_ventana_principal.py``  -> generado con ``pyside6-uic`` (no editar a mano).
* ``main.py`` (este archivo)   -> clase ``Ventana``: lee controles, llama al método,
                                  llena la tabla y las gráficas.
* ``metodo/taylor.py``         -> lógica numérica, sin Qt (la prueba ``pytest``).
* ``graficas.py``              -> dibujos de Matplotlib.
"""
import math
import sys
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QBrush, QColor, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

import casos
import graficas
import textos
from metodo.expresiones import ErrorExpresion
from metodo.taylor import (
    calcular_taylor,
    estudio_truncamiento,
    hallar_h_limite,
    tolerancia_scarborough,
)
from utilidades import exportar_csv, formato_error_pct, formato_valor

RUTA_UI = Path(__file__).parent / "ui" / "ventana_principal.ui"

try:
    # Archivo generado: pyside6-uic ui/ventana_principal.ui -o ui_ventana_principal.py
    from ui_ventana_principal import Ui_MainWindow
except ModuleNotFoundError:
    # Plan B: si aún no se generó el .py, se genera al vuelo desde el .ui.
    from PySide6.QtUiTools import loadUiType

    Ui_MainWindow, _ = loadUiType(str(RUTA_UI))

ENCABEZADOS = [
    "n",
    "Término agregado",
    "Pₙ(x)",
    "Et (verdadero)",
    "εt (%)",
    "εa (%)",
    "Residuo estimado Rₙ",
]
COLOR_FILA_CRITERIO = QColor("#c8e6c9")   # verde claro
COLOR_TEXTO_CRITERIO = QColor("#1b5e20")
# Caracteres permitidos al escribir funciones o números (validación inmediata).
PATRON_EXPRESION = QRegularExpression(r"[0-9A-Za-z_\.\,\+\-\*/\^\(\)\s]*")


class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._resultado = None          # último ResultadoTaylor (para exportar)
        self._caso_actual = {}

        # Lienzos de Matplotlib dentro de los QWidget creados en Designer.
        self.fig_aprox, self.canvas_aprox = self._incrustar(self.ui.widgetGrafica)
        self.fig_error, self.canvas_error = self._incrustar(self.ui.widgetGraficaError)
        self.fig_trunc, self.canvas_trunc = self._incrustar(self.ui.widgetGraficaTrunc)

        self._preparar_tabla()
        self._preparar_validadores()
        self._preparar_textos()
        self._cargar_lista_de_ejemplos()

        # Señales -> métodos
        self.ui.btnCalcular.clicked.connect(self.calcular)
        self.ui.btnLimpiar.clicked.connect(self.limpiar)
        self.ui.btnExportar.clicked.connect(self.exportar)
        self.ui.comboEjemplos.currentIndexChanged.connect(self.cargar_ejemplo)
        self.ui.spinCifras.valueChanged.connect(self._actualizar_tolerancia)

        self.cargar_ejemplo(self.ui.comboEjemplos.currentIndex())

    # ------------------------------------------------------------------ #
    #  Preparación de la ventana
    # ------------------------------------------------------------------ #
    def _incrustar(self, contenedor):
        """Crea un Figure + canvas + barra de herramientas dentro de ``contenedor``."""
        fig = Figure(figsize=(5, 4), layout="constrained")
        canvas = FigureCanvasQTAgg(fig)
        barra = NavigationToolbar2QT(canvas, contenedor)
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(barra)
        layout.addWidget(canvas)
        graficas.limpiar(fig)
        return fig, canvas

    def _preparar_tabla(self):
        tabla = self.ui.tablaResultados
        tabla.setColumnCount(len(ENCABEZADOS))
        tabla.setHorizontalHeaderLabels(ENCABEZADOS)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setAlternatingRowColors(True)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)

    def _preparar_validadores(self):
        for caja in (self.ui.txtFuncion, self.ui.txtX0, self.ui.txtX):
            caja.setValidator(QRegularExpressionValidator(PATRON_EXPRESION, self))

    def _preparar_textos(self):
        self.ui.txtTeoria.setHtml(textos.TEORIA_HTML)
        self.ui.txtAcerca.setHtml(textos.acerca_html())
        self.ui.statusbar.showMessage(textos.barra_estado())

    def _cargar_lista_de_ejemplos(self):
        self._lista_casos = casos.CASOS
        self.ui.comboEjemplos.blockSignals(True)
        for caso in self._lista_casos:
            self.ui.comboEjemplos.addItem(caso["nombre"])
        self.ui.comboEjemplos.setCurrentIndex(casos.CASO_INICIAL)
        self.ui.comboEjemplos.blockSignals(False)

    # ------------------------------------------------------------------ #
    #  Ejemplos y controles
    # ------------------------------------------------------------------ #
    def cargar_ejemplo(self, indice):
        if indice < 0 or indice >= len(self._lista_casos):
            return
        caso = self._lista_casos[indice]
        self._caso_actual = caso
        self.ui.txtFuncion.setText(caso["funcion"])
        self.ui.txtX0.setText(caso["x0"])
        self.ui.txtX.setText(caso["x"])
        self.ui.spinOrden.setValue(caso["n"])
        self.ui.spinCifras.setValue(caso["s"])
        self.ui.spinOrdenEstudio.setValue(caso["n_estudio"])
        self.ui.spinHMax.setValue(caso["h_max"])
        self.ui.spinTolLimite.setValue(caso["tol_limite"])
        self._actualizar_tolerancia()
        self._vaciar_salidas()
        self.ui.txtResultados.setPlainText(
            f"Caso cargado: {caso['nombre']}\n\n{caso['interpretacion']}\n\n"
            "Presiona «Calcular» para ver la tabla, las gráficas y los resultados."
        )

    def _actualizar_tolerancia(self):
        es = tolerancia_scarborough(self.ui.spinCifras.value())
        self.ui.lblEsValor.setText(f"εs = {es:g} %")

    # ------------------------------------------------------------------ #
    #  Acciones de los botones
    # ------------------------------------------------------------------ #
    def calcular(self):
        try:
            n_max = self.ui.spinOrden.value()
            s = self.ui.spinCifras.value()
            n_est = self.ui.spinOrdenEstudio.value()
            h_max = self.ui.spinHMax.value()
            tol = self.ui.spinTolLimite.value()

            res, f_esc, f_vec = calcular_taylor(
                self.ui.txtFuncion.text(),
                self.ui.txtX0.text(),
                self.ui.txtX.text(),
                n_max,
                s,
                n_derivadas=n_est,
            )
            estudio = estudio_truncamiento(
                f_esc, res.derivadas, res.x0, n_est, h_max / 50.0, h_max
            )
            h_limite = hallar_h_limite(f_esc, res.derivadas, res.x0, n_est, tol, h_max)

            self._resultado = res
            self._llenar_tabla(res)
            unidad_x = self._caso_actual.get("unidad_x", "")
            graficas.graficar_aproximacion(self.fig_aprox, f_vec, res, unidad_x)
            graficas.graficar_error_vs_orden(self.fig_error, res)
            graficas.graficar_truncamiento(self.fig_trunc, estudio)
            for canvas in (self.canvas_aprox, self.canvas_error, self.canvas_trunc):
                canvas.draw()
            self._mostrar_resultados(res, estudio, h_limite, tol, n_est)
            self.ui.statusbar.showMessage(
                "Cálculo terminado · " + textos.barra_estado(), 8000
            )
        except (ErrorExpresion, ValueError) as error:
            QMessageBox.warning(self, "Datos no válidos", str(error))
        except Exception as error:  # cualquier fallo inesperado: avisar sin cerrar
            QMessageBox.critical(self, "Error inesperado", f"{type(error).__name__}: {error}")

    def limpiar(self):
        """Borra tabla, gráficas y resultados, y restaura los datos del ejemplo."""
        self.cargar_ejemplo(self.ui.comboEjemplos.currentIndex())

    def exportar(self):
        if self._resultado is None:
            QMessageBox.information(
                self, "Exportar CSV", "Primero presiona «Calcular» para tener resultados."
            )
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar tabla a CSV", "resultados_taylor.csv", "Archivos CSV (*.csv)"
        )
        if not ruta:
            return
        filas = [
            [f.n, f.termino, f.pn, f.et, f.et_pct, f.ea_pct, f.rn]
            for f in self._resultado.filas
        ]
        try:
            exportar_csv(ruta, ENCABEZADOS, filas)
        except OSError as error:
            QMessageBox.warning(self, "No se pudo guardar", str(error))
            return
        self.ui.statusbar.showMessage(f"Tabla exportada a {ruta}", 8000)

    # ------------------------------------------------------------------ #
    #  Salidas: tabla, gráficas y panel de resultados
    # ------------------------------------------------------------------ #
    def _vaciar_salidas(self):
        self._resultado = None
        self.ui.tablaResultados.setRowCount(0)
        for fig, canvas in (
            (self.fig_aprox, self.canvas_aprox),
            (self.fig_error, self.canvas_error),
            (self.fig_trunc, self.canvas_trunc),
        ):
            graficas.limpiar(fig)
            canvas.draw()

    def _llenar_tabla(self, res):
        tabla = self.ui.tablaResultados
        tabla.setRowCount(len(res.filas))
        for i, fila in enumerate(res.filas):
            textos_fila = [
                str(fila.n),
                formato_valor(fila.termino),
                formato_valor(fila.pn),
                formato_valor(fila.et),
                formato_error_pct(fila.et_pct),
                formato_error_pct(fila.ea_pct),
                formato_valor(fila.rn),
            ]
            for j, texto in enumerate(textos_fila):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if res.n_cumple is not None and fila.n == res.n_cumple:
                    item.setBackground(QBrush(COLOR_FILA_CRITERIO))
                    item.setForeground(QBrush(COLOR_TEXTO_CRITERIO))
                    fuente = item.font()
                    fuente.setBold(True)
                    item.setFont(fuente)
                tabla.setItem(i, j, item)

    def _mostrar_resultados(self, res, estudio, h_limite, tol, n_est):
        caso = self._caso_actual
        unidad = f" {caso['unidad']}" if caso.get("unidad") else ""
        lineas = [
            f"Valor verdadero f(x) = {formato_valor(res.valor_verdadero)}{unidad}   "
            f"(x₀ = {res.x0:.6g}, x = {res.x:.6g}, h = {res.h:.6g})",
        ]
        if res.n_cumple is not None:
            fila = res.filas[res.n_cumple]
            lineas += [
                f"RESULTADO: P{fila.n}(x) = {formato_valor(fila.pn)}{unidad}",
                f"Criterio de Scarborough (s = {res.s} cifras → εs = {res.es_pct:g} %): "
                f"se cumple |εa| < εs con {res.terminos_necesarios} términos (orden n = {fila.n}).",
                f"Error alcanzado: εa = {formato_error_pct(fila.ea_pct)} %,  "
                f"εt = {formato_error_pct(fila.et_pct)} %,  Rₙ estimado = {fila.rn:.3e}",
            ]
        else:
            ultima = res.filas[-1]
            lineas += [
                f"RESULTADO: P{ultima.n}(x) = {formato_valor(ultima.pn)}{unidad}",
                f"Criterio de Scarborough (εs = {res.es_pct:g} %): NO se cumple hasta n = {ultima.n}. "
                "Aumenta el orden máximo o reduce las cifras significativas.",
                f"Error alcanzado: εa = {formato_error_pct(ultima.ea_pct)} %,  "
                f"εt = {formato_error_pct(ultima.et_pct)} %",
            ]

        if math.isfinite(estudio.pendiente):
            lineas.append(
                f"Truncamiento (n = {n_est}): pendiente log-log = {estudio.pendiente:.3f}  "
                f"(esperada n + 1 = {n_est + 1}, es decir O(h^{n_est + 1}))."
            )
        else:
            lineas.append(
                f"Truncamiento (n = {n_est}): el error ya es del tamaño del redondeo; "
                "usa un orden menor o un h máximo mayor para medir la pendiente."
            )

        if h_limite is not None:
            extra = f" ≈ {math.degrees(h_limite):.2f}°" if caso.get("unidad_x") == "rad" else ""
            lineas.append(
                f"Con el polinomio de orden {n_est}, |εt| < {tol:g} % mientras |h| < "
                f"{h_limite:.6g}{extra}."
            )
        else:
            lineas.append(
                f"Con el polinomio de orden {n_est}, |εt| se mantiene < {tol:g} % en todo "
                f"|h| ≤ {self.ui.spinHMax.value():g}."
            )

        if caso.get("interpretacion"):
            lineas += ["", "Interpretación: " + caso["interpretacion"]]
        self.ui.txtResultados.setPlainText("\n".join(lineas))


def main():
    app = QApplication(sys.argv)
    ventana = Ventana()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
