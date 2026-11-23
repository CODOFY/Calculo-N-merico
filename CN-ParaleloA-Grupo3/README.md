# Serie de Taylor y error de truncamiento — Grupo 3

Aplicación de escritorio hecha con Python, PySide6 (interfaz diseñada en Qt Designer), SymPy y Matplotlib.
Aproxima una función con el polinomio de Taylor, muestra cómo baja el error al aumentar el orden y
estudia el error de truncamiento.

**Asignatura:** Cálculo Numérico (MECATR24) · Mecatrónica · Quinto nivel
**Grupo:** 3 · **Paralelo:** A

## Integrantes

- Richard Antonio Marcillo Castro
- Galo Abdul Salmon Carrillo
- Deiker Isai Palma Cedeño

## Caso de aplicación: linealización de un sensor de nivel

El caudal por un orificio es `Q = k·√h`, con `k = 0.6`. Se aproxima esa curva con polinomios de Taylor
alrededor del punto de operación `h₀ = 2 m` y se compara la recta tangente (orden 1) con órdenes
superiores, evaluando en `h = 2.5 m`.

| Orden | Pₙ(2.5) | Error εₜ |
|---|---|---|
| 0 | 0.848528137 | 10.6 % |
| 1 (recta tangente) | 0.954594155 | −0.623 % |
| 2 | 0.947965029 | 7.57×10⁻² % |

Valor verdadero: `0.6·√2.5 = 0.948683298`. Con 3 cifras significativas (εₛ = 0.05 %) se necesitan 5 términos.

El selector de ejemplos de la ventana trae este caso y el ejemplo del libro (`cos x`, `x₀ = π/4`, `x = π/3`).

## Instalación (Python 3.10 o superior)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## Cómo ejecutarlo

```bash
python main.py                  # abre la aplicación
python tools/consola.py         # el método en consola, sin interfaz
pytest -v                       # pruebas
```

Si se modifica el diseño en Qt Designer (`pyside6-designer ui/ventana_principal.ui`), hay que regenerar
el código de la interfaz:

```bash
python tools/generar_ui.py      # equivale a: pyside6-uic ui/ventana_principal.ui -o ui_ventana_principal.py
```

## Cómo se usa

1. Elegir un ejemplo de la lista, o escribir otra función `f(x)`, el punto base `x₀` y el punto `x` (se puede escribir `pi/4`, `sqrt(2)`, etc.).
2. Ajustar el orden máximo `n` (0 a 15) y las cifras significativas `s`.
3. Presionar **Calcular**. La pestaña *Tabla* muestra `n`, el término agregado, `Pₙ(x)`, `Eₜ`, `εₜ`, `εₐ` y el residuo `Rₙ`; la fila donde se cumple `|εₐ| < εₛ` queda resaltada. Las otras pestañas grafican `f` con `P₀ … Pₙ`, `|εₜ|` contra `n` y `|Eₜ|` contra `h` en escala log-log.
4. El panel *Resultados* da la respuesta final, el número de términos, el error alcanzado y la interpretación física.
5. **Exportar CSV** guarda la tabla y **Limpiar** borra los resultados y restaura el ejemplo.

Si el texto de la función no es válido se muestra un cuadro de aviso y el programa sigue funcionando.

## Estructura

```
CN-ParaleloA-Grupo3/
├── README.md
├── requirements.txt
├── main.py                    # arranca la aplicación (clase Ventana)
├── info_equipo.py             # integrantes, grupo, paralelo
├── ui/
│   └── ventana_principal.ui   # diseño hecho en Qt Designer
├── ui_ventana_principal.py    # generado con pyside6-uic (no se edita a mano)
├── metodo/
│   ├── __init__.py
│   ├── taylor.py              # lógica numérica, sin Qt
│   └── expresiones.py         # texto -> SymPy (derivadas, lambdify)
├── graficas.py                # funciones de Matplotlib
├── casos.py, textos.py, utilidades.py
├── tests/test_metodo.py       # pruebas con pytest
├── tools/                     # generar_ui.py, consola.py
├── docs/                      # explicación de los cálculos y del código (Word)
└── capturas/                  # imágenes de la interfaz funcionando
```

La lógica numérica (`metodo/taylor.py`) no importa nada de Qt, por eso se puede probar con `pytest`.
Solo `main.py` conoce la interfaz. La explicación completa de los cálculos y del código está en
`docs/Explicacion_Taylor_Grupo3.docx`.

## Capturas

Las capturas de la interfaz funcionando van en la carpeta `capturas/` y se enlazan aquí:

`![Ejemplo del libro](capturas/01_ejemplo_libro.png)`
`![Sensor de nivel](capturas/02_sensor_nivel.png)`
`![Gráficas](capturas/03_graficas.png)`

## Referencia

Chapra, S. y Canale, R., *Métodos numéricos para ingenieros*, caps. 3 y 4.
