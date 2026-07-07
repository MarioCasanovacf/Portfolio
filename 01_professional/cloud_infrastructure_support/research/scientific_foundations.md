# Fundamentos Científicos — Cloud Infrastructure Support

**Fecha:** 2026-06-28  
**Propósito:** Base argumental para `hci-support.mdx`; referencia para los 5 notebooks.

---

## El marco unificador: Kingman's VUT Equation

```
W_q ≈ V × U × T
```

- **V** = factor de variabilidad: (c²_a + c²_s) / 2
- **U** = factor de utilización: ρ/(1−ρ) — nonlinear. A ρ=0.95 → U=19. A ρ=0.99 → U=99
- **T** = tiempo de servicio medio

Al 95% de utilización cualquier variabilidad se multiplica por 19. Los SLOs existen para impedir que ρ se aproxime a 1. Las 7 herramientas de este análisis atacan el mismo sistema desde ángulos complementarios: SPC reduce V; la distribución log-normal de TTR determina c²_s; Erlang C cuantifica cómo V y U producen tiempo de espera; SARIMA predice λ(t) para controlar ρ; el error budget es la política que mantiene ρ < 1 con margen. Little's Law (L = λW) conecta todas las métricas como ley de conservación de flujo.

**Fuentes:**
- Kingman, J.F.C. (1961). The single server queue in heavy traffic. *Mathematical Proceedings of the Cambridge Philosophical Society*, 57(4), 902–904.
- Hopp, W.J. & Spearman, M.L. (1996/2008). *Factory Physics*, 3ª ed. Waveland Press. Caps. 7–9.
- Little, J.D.C. (1961). A proof for the queuing formula L = λW. *Operations Research*, 9(3), 383–387.

---

## Herramienta 1: SPC — Statistical Process Control

**Origen:** Walter A. Shewhart, Bell Telephone Laboratories, 1924. Formalizado: *Economic Control of Quality of Manufactured Product*, D. Van Nostrand, 1931.

**Base matemática:** El límite ±3σ no asume normalidad.
- Chebyshev: P(|X−μ| > 3σ) ≤ 1/9 = 11.1% — distribución libre
- Vysochanskii-Petunin: ≤ 5.5% para distribuciones unimodales
- Shewhart: decisión económica (costo de falsas alarmas vs. incidentes no detectados)

**Qué debes saber:** Distingue variación de causa común (ruido inherente) de causa especial (señal que requiere acción). En términos VUT: una métrica en control tiene c²_s estabilizado. El gráfico de individuos (X-chart) es el más sensible a no-normalidad.

**Modo de falla crítico:** Autocorrelación → límites artificialmente estrechos → avalanchas de falsas alarmas. Alwan & Roberts (1988) demostraron esto empíricamente con datos de telemetría. **Corrección:** aplicar SPC sobre residuos de un modelo ARIMA.

**Citas:**
- Shewhart, W.A. (1931). *Economic Control of Quality of Manufactured Product*. D. Van Nostrand.
- Alwan, L.C. & Roberts, H.V. (1988). Time-series modeling for statistical process control. *Journal of Business and Economic Statistics*, 6(1), 87–95.
- Montgomery, D.C. (2009). *Introduction to Statistical Quality Control*, 6ª ed. Wiley.

---

## Herramienta 2: GESD — Generalized Extreme Studentized Deviate

**Origen:** Bernard Rosner, Harvard School of Public Health, 1983.

**Estadístico:** Rᵢ = max|xⱼ − x̄⁽ⁱ⁾| / s⁽ⁱ⁾. Valores críticos λᵢ derivados de distribución t vía corrección Bonferroni. Detecta hasta k outliers sin masking flaw del ESD simple.

**Qué debes saber:** Requiere que los datos excluyendo outliers sean normales. Twitter (S-H-ESD, 2017) añadió descomposición STL + MAD antes de GESD para manejar autocorrelación y estacionalidad en telemetría.

**Modos de falla:** Supone normalidad en no-outliers; autocorrelación → falsos positivos; colas pesadas → outliers perdidos; k debe especificarse de antemano (masking si k muy bajo).

**Citas:**
- Rosner, B. (1983). Percentage points for a generalized ESD many-outlier procedure. *Technometrics*, 25(2), 165–172. doi:10.1080/00401706.1983.10487848
- Hochenbaum, J., Vallis, O.S. & Kejariwal, A. (2017). Automatic Anomaly Detection in the Cloud Via Statistical Learning. arXiv:1704.07706.
- ASTM D7915-22. Standard Practice for Application of Generalized Extreme Studentized Deviate (GESD) Technique.

---

## Herramienta 3: Distribución Log-Normal del TTR

**Cadena de evidencia:**

| Contribución | Fuente |
|---|---|
| Observación de proceso multiplicativo | Galton (1879); McAlister (1879, *Proc. Royal Society* 29:365) |
| Ley del efecto proporcional → CLT → log-normal | Gibrat (1931). *Les Inégalités Économiques* |
| Monografía matemática canónica | Aitchison & Brown (1957). *The Lognormal Distribution*. Cambridge UP |
| Validación empírica en hardware (70 datasets) | Kline (1984). *Reliability Engineering* 9:65–80. doi:10.1016/0143-8174(84)90041-6 |
| Validación en software/IT | Grottke & Trivedi (2009). *IEEE Computer* 40(2):107–109 |
| Estándar DoD | MIL-HDBK-338B §5.6.2.1 (US Dept. of Defense, 1998) |

**Por qué TTR es multiplicativo:** TTR = diagnóstico × localización × reparación × verificación. Cada factor escala proporcionalmente al anterior. Por CLT: ln(TTR) = Σln(Xᵢ) → Normal → TTR ~ LogNormal. No es un supuesto conveniente — es consecuencia derivable del proceso.

**Qué debes saber:** 
- MTTR = exp(μ + σ²/2) — media siempre > mediana (exp(μ))
- Mediana = "tiempo típico de resolución"
- Media = capacidad de throughput para dimensionar staffing
- La cola derecha no es artefacto del dato; es el costo de incidentes complejos

**Modos de falla:** Pasos aditivos (no multiplicativos) → Weibull o gamma; con datos censurados → análisis de supervivencia; mezcla de tipos de incidente → distribuciones mixtas.

---

## Herramienta 4: Erlang C (Cola M/M/c)

**Origen:** Agner Krarup Erlang, Copenhagen Telephone Company. Paper de 1909 (distribución Poisson de llamadas); paper definitivo de 1917.

**Fórmula:**

```
C(c, a) = [aᶜ/c! · 1/(1−ρ)] / [Σₖ₌₀^{c−1} aᵏ/k! + aᶜ/c! · 1/(1−ρ)]

P(espera > t) = C(c, a) · e^(−(cμ−λ)t)
```

donde a = λ/μ (carga en Erlangs), ρ = a/c < 1 para estabilidad.

**Qué debes saber:** Responde directamente: con λ incidentes/hora, MTTR de μ minutos, y c ingenieros disponibles, ¿qué porcentaje espera más de t minutos? El resultado es escenario hipotético — los supuestos de Poisson + exponencial casi nunca se cumplen en NOC. Su valor es dar el piso teórico.

**Violaciones y consecuencias:**

| Supuesto | Violación | Fuente |
|---|---|---|
| Llegadas Poisson | Incidentes bursty (varianza > media) | Jongbloed & Koole (2001) |
| Servicio exponencial | TTR log-normal (c²_s > 1) | Brown et al. (2005, *JASA* 100:36–50) |
| Paciencia infinita | Con 5% abandono: error de 55× | Robbins et al. (2010, WSC) |
| λ constante | Ciclos diario/semanal | Green, Kolesar & Soares (2001, *Management Science*) |

**Citas:**
- Erlang, A.K. (1917). Solution of some problems in the theory of probabilities. *Post Office Electrical Engineers' Journal*, 10, 189–197.
- Robbins, T.R., Medeiros, D.J. & Harrison, T.P. (2010). A simulation study of Erlang-C and Erlang-A for call center workforce scheduling. *Proc. Winter Simulation Conference*.
- Brown, L. et al. (2005). Statistical analysis of a telephone call center. *JASA*, 100(469), 36–50.

---

## Herramienta 5: SARIMA

**Origen:** Box & Jenkins (1970). Sintetiza Yule (AR, 1926), Slutsky (MA, 1937), Wold (descomposición, 1938).

**Modelo:** SARIMA(p,d,q)(P,D,Q)_s — diferenciación d veces + diferenciación estacional D veces → estacionaridad → AR + MA + AR_estacional + MA_estacional.

**Qué debes saber:** Predice λ(t) — el volumen de tickets/incidentes por período — para dimensionar staffing antes de que llegue la demanda. Sin predicción de λ(t), Erlang C solo responde preguntas retroactivas. SARIMA cierra el ciclo.

**Modos de falla:**
- Roturas estructurales (migraciones, outages grandes) → modelo inútil post-evento
- Datos de conteo con ceros → INGARCH > SARIMA
- Múltiples estacionalidades solapadas → TBATS o Prophet
- Intervalos de predicción: cobertura empírica 71–87% (no 95% nominal) — Hyndman (2002)
- M4 Competition (2018): ARIMA ranked 20th de 61 métodos; métodos de ensamble ganaron con margen

**Citas:**
- Box, G.E.P. & Jenkins, G.M. (1970). *Time Series Analysis: Forecasting and Control*. Holden-Day.
- Hyndman, R.J. (2002). It's time to move from "what" to "why." *International Journal of Forecasting*, 18(4), 567–570.
- Makridakis, S. et al. (2018). The M4 Competition. *International Journal of Forecasting*, 34(4), 802–808.

---

## Herramienta 6: Error Budget

**Origen:** Beyer, B., Jones, C., Petoff, J. & Murphy, N.R. (Eds.) (2016). *Site Reliability Engineering*, O'Reilly. Capítulo 3: "Embracing Risk." [sre.google/sre-book/embracing-risk/]

**Definición:** Error Budget = 1 − SLO. Un SLO de 99.9% en ventana de 30 días = 43.2 minutos de inactividad permitida. Cuando el presupuesto se agota → se frena velocity de features.

**Base teórica subyacente (no en el libro):** Proceso de renovación alternante. lim A(t) = E[uptime] / (E[uptime] + E[downtime]). La disponibilidad asintótica depende de las medias — no de las distribuciones completas.

**Qué debes saber:** Es política operacional bien diseñada, no estadística inferencial. Su poder no es matemático sino organizacional: da al SRE autoridad para decir "no" a nuevos deploys sin argumento técnico caso a caso. Frenar deploys reduce el ritmo de cambio → reduce c²_s → reduce V en VUT.

**Modos de falla:** SLO mal calibrado → budget siempre lleno o vacío; sin enforcement organizacional → métrica decorativa.

**Cita:**
- Beyer et al. (2016). *Site Reliability Engineering*, O'Reilly, Cap. 3. Disponible: sre.google/sre-book/embracing-risk/

---

## Herramienta 7: Métricas DORA

**Origen:** Forsgren, N., Humble, J. & Kim, G. (2018). *Accelerate: The Science of Lean Software and DevOps*. IT Revolution Press. n ≈ 23,000 respuestas de encuesta, 2014–2017.

**Método:** PLS-SEM (Partial Least Squares Structural Equation Modeling) + análisis factorial exploratorio. Cuatro grupos (elite/high/medium/low) vía clustering jerárquico (Ward).

**Qué debes saber:** Las afirmaciones son correlacionales. El lenguaje causal en las figuras no está respaldado por el diseño cross-sectional. Keunwoo Lee (2018) documentó: "inferential predictive" no está en la taxonomía de Leek que los autores citan; umbral p < 0.10 en lugar del convencional 0.05; halo effects en self-report; constructo no validado independientemente. **Uso correcto:** benchmarks de calibración (¿en qué rango cae nuestro MTTR vs. la industria?), no prueba de causalidad.

**Citas:**
- Forsgren, N., Humble, J. & Kim, G. (2018). *Accelerate*. IT Revolution Press.
- Lee, K. (2018). Reviewing Accelerate's statistical claims. keunwoo.com/blog/2018/accelerate-review
- Leek, J.T. & Peng, R.D. (2015). What is the question? *Science*, 347(6228), 1314–1315.

---

## Zona gris — interesante pero no comprometido

1. **Kingman (1961) "exacto" vs. VUT "pedagógico":** El paper original de Kingman prueba el resultado para G/G/1 en heavy traffic; la forma W_q = V·U·T es la adaptación pedagógica de Hopp & Spearman. Matemáticamente equivalente; presentación distinta. Importa solo si alguien busca la fórmula literal en el paper original.

2. **Erlang A para NOC:** Erlang A (M/M/n+M con abandono) es formalmente superior a Erlang C cuando existen timeouts o escalaciones. La transferencia a contexto NOC/SRE es directa pero no hay paper que lo aplique explícitamente en ese contexto.

3. **MIL-HDBK-338B §5.6.2.1:** Cita ampliamente usada en literatura secundaria; texto completo del manual DoD no verificado directamente. Kline (1984) es la fuente primaria sólida.

4. **Respuesta de DORA a crítica Lee (2018):** No encontré respuesta pública formal de los autores.

---

## Alto aquí — no investigues más

| Tema | Razón |
|---|---|
| Demostración formal de Little's Law | Ley de conservación universal sin supuestos restrictivos; más investigación tiene cero upside |
| Derivación de Erlang C vía CTMC | Lo que importa es cuándo falla; el público objetivo acepta la fórmula como establecida |
| Debate DORA vs. Lee | Irrelevante si usas DORA como calibración, no inferencia causal |
| Network calculus / geometría estocástica | Requiere datos de tracing distribuido — no disponibles en el stack actual |
| Stack Bayesiano para reliability | Proyecto diferente de naturaleza; costo > beneficio para este portfolio |

---

## Dos lecturas prioritarias antes del MDX

1. **Hopp & Spearman, *Factory Physics* (3ª ed., 2008)** — Caps. 7–9: VUT, Law of Variability, Buffering Law. Hace explícita la conexión SPC ↔ queueing ↔ reliability.
2. **Koole & Mandelbaum (2002). "Queueing Models of Call Centers." *Annals of Operations Research* 113:41–59.** PDF libre en math.vu.nl/~koole/publications/2002aor/aor.pdf — encuesta más clara sobre por qué M/M/c falla en operaciones reales.
