# Heston / Opciones Exóticas — evaluación de publish-readiness

**Notebook:** `notebooks/02_Exotic_Options_Heston.ipynb`
**Fecha de ejecución:** 2026-07-05
**Comando de ejecución (reproducible):**

```
cd /Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/01_professional/quantitative_finance/notebooks
/Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/.venv/bin/jupyter nbconvert --execute --inplace --ExecutePreprocessor.timeout=600 02_Exotic_Options_Heston.ipynb
```

**Resultado:** exit code 0, sin errores en ninguna celda. Los tres bloques de output
(simulación, precio Monte Carlo antitético, comparación con Monte Carlo plano) se
regeneraron con los mismos valores que antes de correr (seed=42 fijo → determinista):

- Precio Asian call (antitético): \$5.2019, SE ±\$0.0186
- Precio Asian call (naive MC, mismo presupuesto de paths): \$5.2516, SE ±\$0.0294
- corr(payoff, mirror payoff) = −0.598
- ratio SE_naive/SE_antitético = 1.58x (~2.5x menos paths para el mismo error estándar)

No hay dependencia rota de `site/` en este notebook: no usa `FIG_DIR`, `REPO_ROOT.parent`
ni ningún `savefig` hacia site — el problema de path que afecta a
`03_Hierarchical_Risk_Parity.ipynb` (T-105) **no aplica aquí**. No hice ningún cambio de
código en este notebook; la ejecución fue limpia sin intervención.

---

## 1. ¿Responde una pregunta real, o es una tautología?

La pregunta que el notebook realmente contesta es metodológica, no de mercado:
**¿cuánta reducción de varianza logran los antithetic variates al pricear una Asian call
bajo Heston con simulación Euler–Maruyama, y por qué?**

Esto es una pregunta real y falsificable en el sentido correcto:

- El resultado (1.58x, corr=−0.598) se **mide**, no se asume. El notebook corre ambos
  estimadores (antitético y naive) con el mismo presupuesto de paths y calcula la
  correlación empírica entre cada path y su espejo — no declara el mecanismo, lo verifica.
- La dirección del efecto (reducción de varianza vía antithetic con payoff monótono) es
  un resultado matemático conocido y esperado — eso es inherente a la técnica, no algo que
  el notebook "diseñó para que funcione" de forma oculta. Lo honesto aquí es que el
  notebook lo dice explícitamente ("The gain isn't a lucky seed; it has a mechanism"),
  en vez de presentar el resultado como un descubrimiento sorpresivo.
- El notebook es explícito sobre el alcance: "the inputs are illustrative rather than
  calibrated to any market... not a production pricer." No hay ninguna afirmación
  encubierta de valor de mercado ni de que este sea un pricer utilizable en producción.

**Veredicto: no es una tautología.** Es una demostración pedagógica honesta de una técnica
de reducción de varianza, con el resultado cuantitativo medido en vez de asumido, y sin
pretender ser más que eso.

## 2. ¿Los datos sintéticos están declarados como benchmark, con parámetros del generador?

Sí, con matices:

- Todos los parámetros del generador están impresos en el código y son visibles en el
  notebook ejecutado: `S0=100, v0=0.04, kappa=2.0, theta=0.04, xi=0.3, rho=-0.7, r=0.03,
  T=1.0, M=252, N=50000`, con `np.random.seed(42)` fijo para reproducibilidad estricta.
- La celda de síntesis (`### Synthesis`) declara explícitamente que los inputs son
  "illustrative rather than calibrated to any market" — esto satisface la regla de
  declarar el dato sintético como benchmark y no como hallazgo de mercado.
- **Matiz:** la declaración de "benchmark" aparece en prosa (celda 0 y celda de síntesis),
  no en un bloque de parámetros aislado y etiquetado como tal. Es suficiente para lectura
  atenta, pero un lector que solo mire el código (celda 3) vería una lista de parámetros
  sin la etiqueta "estos son ilustrativos, no calibrados" al lado — la etiqueta está en la
  celda de markdown anterior, no en un comentario en la celda de código misma. Esto es una
  brecha menor de forma, no de fondo.

## 3. ¿Corre limpio end-to-end?

Sí. Confirmado por ejecución real (ver comando y exit code arriba). Sin excepciones, sin
warnings bloqueantes — el único warning es
`UserWarning: FigureCanvasAgg is non-interactive, and thus cannot be shown`, esperado en
ejecución headless vía nbconvert (`plt.show()` sin backend interactivo) y no afecta el
resultado ni la figura embebida en el notebook.

## 4. Qué está publish-ready

- La narrativa central (variance reduction medida y explicada mecánicamente) es sólida,
  honesta y no infla el resultado.
- La declaración de límites en la celda de síntesis es exactamente el tipo de honestidad
  que este workspace exige: sesgo de discretización Euler–Maruyama reconocido, inputs
  ilustrativos reconocidos, y el propio autor dice "I'd trust the mechanism demonstrated
  here well before I'd trust the price itself."
- Reproducibilidad estricta (seed fijo, misma ejecución → mismos números).
- Sin dependencia rota de rutas (`site/`), a diferencia del notebook HRP.

## 5. Brechas para full-quality (no cortes de alcance, solo lo que falta)

1. **Comentario huérfano de "sensitivity analysis":** la celda 1 tiene el comentario
   `# Strict reproducibility for sensitivity analysis` pero el notebook no contiene ningún
   sweep de sensibilidad (por ejemplo, variar `rho` de −0.9 a 0 y mostrar cómo cae la
   reducción de varianza a medida que el leverage effect se debilita). El comentario
   promete algo que el notebook no entrega — o es un resto de una versión anterior, o es
   una extensión pendiente. Vale la pena resolverlo antes de publicar: o se agrega el
   sweep, o se corrige/elimina el comentario.
2. **Ratio de reducción de varianza reportado como punto único, sin su propia
   incertidumbre:** el 1.58x viene de una sola corrida con seed=42. La reducción de
   varianza es en sí una cantidad con variabilidad muestral — correr con varios seeds y
   reportar el ratio promedio ± rango daría más robustez a la afirmación cuantitativa
   ("aproximadamente 1.6x", no "1.58x exacto").
3. **Sesgo de discretización mencionado pero no cuantificado:** el notebook reconoce el
   sesgo de Euler–Maruyama (M=252 pasos) como límite pero no lo mide (por ejemplo,
   comparando M=252 vs. M=1000, o usando el discretization scheme QE de Andersen). Esto es
   honesto como está, pero es una extensión natural para "full quality" si Mario quiere
   fortalecer la robustez metodológica.
4. **Extensiones ya autodeclaradas pero no implementadas:** el propio notebook nombra dos
   extensiones (control variate con el precio cerrado del Asian geométrico, y Greeks vía
   diferencias finitas con common random numbers) como trabajo futuro. Estas no son un
   defecto — están correctamente etiquetadas como fuera de alcance — pero quedan como
   gaps explícitos si se busca ampliar el caso de estudio antes de publicarlo.
5. **Etiqueta de benchmark sintético en prosa, no en el código:** ver punto 2 de la
   sección anterior — mover o duplicar la declaración de "inputs ilustrativos, no
   calibrados" como comentario en la celda de parámetros reforzaría la trazabilidad para
   un lector que salte directo al código.

## 6. Fuera de alcance de esta tarea (T-111)

No se escribió `site/src/pages/case-studies/heston.mdx` ni se tocó `studies.ts` — esa
prosa es Mario-gated (T-118). No se hizo commit/push. No se tocó
`03_Hierarchical_Risk_Parity.ipynb` (T-105) ni ningún archivo fuera del árbol
`quantitative_finance`.

## Veredicto general

**Publish-ready en su núcleo metodológico**, con brechas menores de forma (comentario
huérfano, ratio sin banda de incertidumbre) que no bloquean publicación pero que valdría
la pena resolver para el estándar de "full quality, sin cortes" de este workspace. No hay
riesgo de tautología ni de dato sintético sin declarar — ambos puntos críticos del
protocolo de revisión están cubiertos correctamente por el propio notebook.
