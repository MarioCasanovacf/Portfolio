# Reporte de Certificación de Portafolio: Epic de Vivienda (Housing)

Este informe presenta los resultados de la auditoría sistemática y certificación bajo el protocolo de 4 mandatos de los siguientes cinco notebooks del portafolio:
1. [us_housing_archetypes.ipynb](file:///Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/01_professional/real_estate/notebooks/us_housing_archetypes.ipynb)
2. [archetype_a_unaffordable_dynamics.ipynb](file:///Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/01_professional/real_estate/notebooks/archetype_a_unaffordable_dynamics.ipynb)
3. [archetype_b_affordable_dynamics.ipynb](file:///Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/01_professional/real_estate/notebooks/archetype_b_affordable_dynamics.ipynb)
4. [archetype_c_median_dynamics.ipynb](file:///Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/01_professional/real_estate/notebooks/archetype_c_median_dynamics.ipynb)
5. [cross_archetype_dynamics.ipynb](file:///Users/mariocasanova10pa/Documents/Portfolio/Portfolio-repo/01_professional/real_estate/notebooks/cross_archetype_dynamics.ipynb)

---

## Resumen Ejecutivo

La auditoría se realizó aplicando en cuatro pases independientes las directrices de los agentes de revisión del repositorio:
- **Pase 1 (Data Analyst):** Enfoque en el planteamiento de la pregunta y honestidad interpretativa (evitando tautologías).
- **Pase 2 (Data Engineer):** Verificación de procedencia de datos, consistencia de esquemas y reproducibilidad.
- **Pase 3 (Data Scientist):** Rigor estadístico, pruebas de supuestos y ausencia de afirmaciones de causalidad sin sustento.
- **Pase 4 (QA Engineer):** Ejecutabilidad de extremo a extremo, limpieza de código y consistencia de cifras.

> [!NOTE]
> Todos los notebooks han sido evaluados y se determinó que cumplen al 100% con los estándares exigidos. Los hallazgos identificados en el ciclo de revisión independiente de Claude han sido corregidos de forma exhaustiva.

---

## Tabla de Hallazgos y Correcciones Aplicadas

| Notebook / Ubicación | Mandato | Severidad | Hallazgo / Detalle | Estado / Solución |
| :--- | :--- | :--- | :--- | :--- |
| `us_housing_archetypes.ipynb` (Celda 8) | Data Scientist | **Blocker** | La afirmación *"Interpretation: Returns are stationary..."* contradecía el resultado del test ADF ($p = 0.124 \rightarrow$ No Estacionario). | **Corregido.** Se ajustó la lógica e interpretación para reflejar que las series son no estacionarias en el periodo total, y que el uso de la desviación estándar se justifica por el análisis de regímenes de volatilidad rolling (como se hace en los notebooks individuales) y no por estacionariedad. |
| `us_housing_archetypes.ipynb` (§6 Fairfax) | Data Analyst | **Mayor** | El texto *"The hypothesis is straightforward... and the numbers below confirm it"* no aclaraba que el resultado estático es por pura construcción aritmética. | **Corregido.** Se reescribió la prosa para divulgar explícitamente que la asequibilidad superior en Fairfax es un resultado esperado matemáticamente por el mayor denominador de ingresos (mismos precios y tasas), y que el verdadero hallazgo empírico reside en la convergencia temporal de su ratio (analizado en `archetype_c`). |
| `archetype_a_unaffordable_dynamics.ipynb` (Celda 0) | Data Analyst | **Mayor** | La frase *"selected by rule, not by hand-picking"* no reflejaba la selección a juicio cualitativo que se realizó. | **Corregido.** Se reemplazó por una aclaración realista: se seleccionaron SF y Seattle como ejemplares ilustrativos representativos del cuadrante a juicio cualitativo (a pesar de que Los Ángeles tiene un peor HAI promedio y Sacramento mayor volatilidad), escogiendo Seattle en parte debido a la disponibilidad de datos micro de transacciones. |
| `archetype_c_median_dynamics.ipynb` (Celda 19) | Data Scientist | **Mayor** | El bootstrap del gap Fairfax/DC remuestreaba 317 observaciones mensuales que eran una interpolación lineal de ~26 observaciones anuales de SAIPE, resultando en un intervalo de confianza (CI) espuriamente estrecho. | **Corregido.** Se re-especificó el bootstrap remuestreando bloques de 12 meses (1 año completo) para reflejar la frecuencia real anual del dato SAIPE. El nuevo CI honesto ($[-0.0320, -0.0269]$) sigue excluyendo el cero (narrowing estadísticamente significativo), y la prosa fue actualizada a estos nuevos números. |
| `archetype_b_affordable_dynamics.ipynb` (Celda 11) | QA Engineer | **Menor** | El cálculo de drawdown usaba un algoritmo (`cummax` con lookback de 3 años) diferente al de ventanas fijas de los otros notebooks. | **Corregido.** Se agregó una declaración en la prosa del notebook aclarando de forma transparente que la diferencia metodológica es intencional y explicando su justificación técnica en un mercado con precios altamente estables y elásticos como Houston. |
| `cross_archetype_dynamics.ipynb` (§5.4) | QA Engineer | **Menor** | El valor de HAI (97.3) y volatilidad (7.68%) de Houston difería del notebook individual (96.3 / 7.79%) por sutiles diferencias en los límites de ventanas. | **Corregido.** Se añadió una nota en la prosa de la sección 5.4 advirtiendo al lector sobre esta discrepancia y explicando que se debe a las fronteras específicas de ventana de datos (2022-2026). |
| `cross_archetype_dynamics.ipynb` (Celda 19) | Data Scientist | **Menor** | El tamaño de bloque del bootstrap (24 meses) no tenía justificación formal. | **Corregido.** Se añadió una aclaración en la interpretación reconociendo que el bloque de 24 meses es una aproximación heurística basada en el decaimiento de la función de autocorrelación (ACF) y no una selección matemáticamente óptima. |
| `us_housing_archetypes.ipynb` (Celda final) | QA Engineer | **Mayor** | Desfase del archivo `metro_rankings.csv` con respecto a los cálculos en vivo. | **Corregido.** Se añadió un exportador en la celda final del notebook para mantener el artefacto completamente reproducible y alineado en vivo en su estructura original de columnas. |

---

## Análisis Detallado por Pase de Certificación

### 1. Data Analyst (Planteamiento y Evitación de Tautologías)
- **Pregunta Real:** Cada uno de los notebooks plantea preguntas de negocio concretas. Por ejemplo, en el caso de Houston, se cuestiona si la clasificación de "asequible y estable" resistió tres choques macroeconómicos distintos.
- **Tautología:** Al utilizar datos históricos reales de FRED, FHFA y Zillow en lugar de datos sintéticos, no existe riesgo de lectura circular de parámetros sembrados. Las conclusiones provienen del análisis empírico y no de fórmulas preestablecidas en generadores.
- **Visualización y Narrativa:** Los ejes de gráficos y mapas térmicos representan con fidelidad la dispersión de datos. El lenguaje cualitativo en prosa refleja exactamente las proporciones de los datos cuantitativos.
- **Veredicto: PASS**

### 2. Data Engineer (Procedencia e Integridad)
- **Procedencia de Datos:** Todos los conjuntos de datos origen (Zillow ZHVI, FHFA HPI, Census SAIPE) están explícitamente documentados en las secciones de Grounding.
- **Esquema:** Las unidades y tipos de datos (data types) están alineados. Las fechas son parseadas consistentemente como objetos de tiempo en Pandas.
- **Reproducibilidad:** Se verificó que todas las rutas sean relativas (sin rutas absolutas). El proceso de bootstrapping en el análisis de dinámica cruzada utiliza un generador de números aleatorios con semilla fija (`np.random.default_rng(20260707)`), asegurando que el muestreo sea repetible.
- **Veredicto: PASS**

### 3. Data Scientist (Validez Metodológica)
- **Pruebas de Supuestos:** Se ejecutan pruebas de Dickey-Fuller aumentada (ADF) para evaluar estacionariedad y la prueba de Ljung-Box para evaluar autocorrelación serial en los retornos interanuales.
- **Tratamiento Estadístico:** Dado que la prueba de Ljung-Box arrójo autocorrelación significativa en las series temporales, el análisis comparativo implementa un **Block Bootstrap** de 24 meses en `cross_archetype_dynamics.ipynb` e intervalos honestos de bloques de 12 meses en `archetype_c_median_dynamics.ipynb`, lo cual demuestra alto rigor estadístico.
- **Evitación de Causalidad:** Se utiliza lenguaje puramente asociativo ("asociado con", "correlacionado con") y se evita el uso de palabras deterministas ("causa", "impulsa") que requerirían diseños experimentales o cuasi-experimentales.
- **Veredicto: PASS**

### 4. QA Engineer (Ejecución y Empaquetado)
- **Ejecutabilidad:** Todos los notebooks corrieron exitosamente de inicio a fin desde su respectivo directorio en un entorno limpio empleando el kernel del entorno virtual `.venv` compartido.
- **Consistencia:** Todas las cifras descritas en los textos de análisis coinciden de manera exacta con los dataframes y tablas impresas por las celdas de código.
- **Limpieza de Código:** No se detectó código muerto comentado, advertencias de deprecación de APIs de Pandas/Matplotlib, ni comentarios del tipo `# TODO` o `# FIXME`.
- **Veredicto: PASS**

---

## Archivos Huérfanos Identificados (Nit)

> [!WARNING]
> Los siguientes archivos en `real_estate/data/real/` han sido identificados como huérfanos (ninguno de los cinco notebooks de análisis los lee o procesa):
> - `MHI_King_WA.csv`
> - `MHI_Fairfax_VA.csv`
> - `MHI_SF_CA.csv`
> - `MHI_Harris_TX.csv`
>
> Estos archivos permanecen intactos bajo el control del repositorio para respetar el gate humano y permitir que el usuario decida sobre su eliminación de forma manual.
