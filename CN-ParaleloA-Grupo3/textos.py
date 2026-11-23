"""Textos fijos que muestra la interfaz (teoría y «Acerca de»)."""
import info_equipo

TEORIA_HTML = """
<h2>Error de truncamiento vs. error de redondeo</h2>

<h3>Error de truncamiento</h3>
<p>Aparece porque <b>cortamos</b> un proceso infinito. La serie de Taylor tiene
infinitos términos; al quedarnos solo con los primeros <i>n</i>+1 estamos
truncando la serie, y lo que dejamos fuera es el residuo
<i>R<sub>n</sub></i> ≈ f<sup>(n+1)</sup>(x₀)/(n+1)! · h<sup>n+1</sup>.<br>
• <b>Depende del método</b> (el orden <i>n</i>) y de <i>h</i> = x − x₀.<br>
• Disminuye al <b>aumentar n</b> o al <b>reducir h</b>: es O(h<sup>n+1</sup>).<br>
• Existiría incluso con una computadora perfecta, de precisión infinita.</p>

<h3>Error de redondeo</h3>
<p>Aparece porque la computadora guarda los números con <b>un número finito de
cifras</b> (doble precisión ≈ 16 cifras, ε<sub>máq</sub> ≈ 2.2×10⁻¹⁶). Cada
operación puede perder una fracción de la última cifra.<br>
• <b>Depende de la máquina</b> y de cómo se hacen las cuentas, no del orden de la serie.<br>
• No baja al aumentar <i>n</i>; al contrario, restar números casi iguales o sumar
muchos términos lo puede <b>aumentar</b>.<br>
• Es el «piso» que se ve en la gráfica log-log cuando |E<sub>t</sub>| ya no baja.</p>

<h3>Cómo verlo en esta aplicación</h3>
<p>• En la pestaña <b>Error vs n</b>, |ε<sub>t</sub>| baja al subir <i>n</i> (truncamiento).<br>
• En la pestaña <b>Truncamiento</b>, la recta de pendiente <i>n</i>+1 es el error de
truncamiento; los puntos que se aplanan abajo, cerca de 10⁻¹³ a 10⁻¹⁶, son
<b>redondeo</b> y por eso no se usan para calcular la pendiente.</p>

<h3>Fórmulas usadas</h3>
<p>P<sub>n</sub>(x) = Σ f<sup>(k)</sup>(x₀)/k! · h<sup>k</sup>, h = x − x₀<br>
ε<sub>t</sub> = (valor verdadero − P<sub>n</sub>)/valor verdadero · 100 %<br>
ε<sub>a</sub> = (P<sub>n</sub> − P<sub>n−1</sub>)/P<sub>n</sub> · 100 %<br>
ε<sub>s</sub> = 0.5 × 10<sup>(2−s)</sup> % (criterio de Scarborough, s cifras significativas)</p>

<h3>Cómo escribir la función</h3>
<p>Use <code>x</code> como variable y punto decimal (la coma se convierte en punto).
Admite <code>^</code> o <code>**</code> para potencias, <code>exp</code>,
<code>sin</code> (o <code>sen</code>), <code>cos</code>, <code>tan</code>,
<code>sqrt</code> (o <code>raiz</code>), <code>log</code>/<code>ln</code>, y las
constantes <code>pi</code> y <code>e</code>. En x₀ y x puede escribir
<code>pi/4</code>, <code>sqrt(2)</code>, etc.</p>
"""


def acerca_html() -> str:
    filas = "".join(f"<li>{nombre}</li>" for nombre in info_equipo.INTEGRANTES)
    grupo = info_equipo.GRUPO
    return f"""
<h2>Serie de Taylor y error de truncamiento</h2>
<p><b>Asignatura:</b> {info_equipo.ASIGNATURA}<br>
<b>Unidad:</b> {info_equipo.UNIDAD}<br>
<b>Paralelo:</b> {info_equipo.PARALELO} &nbsp;·&nbsp; <b>Grupo:</b> {grupo}</p>
<p><b>Integrantes:</b></p>
<ul>{filas}</ul>
<p>Interfaz diseñada en Qt Designer (archivo <code>ui/ventana_principal.ui</code>),
programada en Python con PySide6. Texto base: Chapra y Canale, <i>Métodos
numéricos para ingenieros</i>, cap. 4.</p>
"""


def barra_estado() -> str:
    grupo = info_equipo.GRUPO
    nombres = ", ".join(info_equipo.INTEGRANTES)
    return (
        f"Grupo {grupo} · Paralelo {info_equipo.PARALELO} · "
        f"{info_equipo.ASIGNATURA} · {nombres}"
    )
