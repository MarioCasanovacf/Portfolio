# Design Doc — Rediseño de las 5 notebooks sobre datos reales

**Fecha:** 2026-06-30 · **Estado:** v1 — revisado por data-analyst (framing) y data-scientist (metodología); fixes incorporados. Ver "Log de revisión" al final.
**Contexto:** El diseño anterior era tautológico (el generador plantaba la señal, la notebook la "descubría"). Este rediseño parte de datos reales capturados de fuentes públicas y de 5 preguntas definidas por Mario ANTES de mirar los resultados.

---

## Persona y pregunta paraguas

**Persona:** El lead de un equipo de soporte/NOC cuya operación depende de servicios cloud de terceros (GitHub, Anthropic, GCP) y de pipelines CI propios. No controla la infraestructura de los proveedores; sí controla su staffing, sus SLOs internos y su política de triaje.

**Pregunta paraguas:** ¿Cómo dimensiono y opero un equipo de soporte cuando parte de mi carga de trabajo la generan fallas de servicios que no controlo?

Esta persona hace decisiones reales: cuántos ingenieros por turno, qué SLO interno prometer, cuándo escalar, qué hacer cuando la cola se llena de tickets bloqueados por el proveedor.

---

## Datos disponibles (capturados 2026-06-27)

### Reales
| Archivo | Filas | Rango | Qué es |
|---|---|---|---|
| `real/github_actions_runs.csv` | 700 | 2026-05-13 → 06-27 (45 días) | Runs reales de GitHub Actions de 7 repos OSS grandes. Cols: repo, workflow, conclusion (success 434 / failure 84 / skipped 83 / action_required 80 / cancelled 19), duration_sec (mediana 39s, p95 830s) |
| `real/service_incidents.csv` | **787** (v2, expandido 2026-07-03) | ventanas variables por proveedor | Incidentes reales de status pages de **18 proveedores**: github, claude_anthropic, gcp + cloudflare, vercel, npm, datadog, twilio, dropbox, discord, linear, atlassian, reddit, openai, digitalocean, circleci, zoom, figma. 774 con duración. Backup del original (103 filas) en scratchpad; expansión también en `staging_service_incidents_expansion.csv` |

**Expansión de proveedores (2026-07-03), consecuencias para el diseño:**
- **NB04 se destranca:** positivos pasan de 25 a **194** (P75 recomputado sobre el set combinado = 209.2 min). EPV deja de ser el cuello de botella; el feature set capado se mantiene por disciplina, pero ahora hay margen para interacciones simples si el modelo base lo justifica.
- **Ventanas de observación por proveedor son distintas** (la API entrega "últimos ~50 incidentes", que cubren 9 días en Twilio y 7 años en Atlassian): NB01 calcula disponibilidad por proveedor SOLO dentro de la ventana propia de cada uno; jamás se comparan tasas entre proveedores sin normalizar por ventana.
- **Caveat Twilio:** 45 incidentes en 9 días con mediana 330 min — probablemente una crisis de plataforma generando incidentes correlacionados. Se mantiene pero se declara; análisis de sensibilidad con/sin Twilio en NB02.
- **Caveat convenciones de impact:** Figma/Atlassian etiquetan casi todo `none`; Discord usa `major` liberalmente. El impact NO es comparable entre proveedores → siempre se acompaña de provider como covariable, nunca se usa solo agregado.
- **Caveat OpenAI:** sin `affected_components` ni `shortlink` (su API no los expone).
- Descartados: Stripe, PagerDuty, Notion (sin API pública compatible), Slack y Heroku (formato propio; adaptador no vale la pena con el rendimiento ya obtenido).

### Sintéticos (rol: baseline calibrado, NO objeto de análisis)
| Archivo | Filas | Qué es |
|---|---|---|
| `synthetic/synthetic_ci_runs.csv` | 3,633 | Calibrado a DORA (failure rate 6.5%), seed 20240401 |
| `synthetic/synthetic_incidents.csv` | 640 | Calibrado a DORA (λ=1.7/día, mediana MTTR 60 min), seed 20240401 |

**Regla anti-tautología para los sintéticos:** solo se usan como *benchmark de comparación* ("el mundo DORA-mediano se vería así; la realidad observada se ve asá"). Ninguna conclusión de las notebooks puede depender de una propiedad plantada en el generador. Toda comparación real-vs-sintético debe declarar el parámetro del generador junto al resultado.

### Limitaciones declaradas de los datos reales
1. **n=103 incidentes, ~9 semanas.** Suficiente para distribuciones y descriptivos; marginal para estacionalidad semanal (9 ciclos); insuficiente para estacionalidad mensual/anual.
2. **GCP se excluye** de todo análisis de duración (3 incidentes, 0 con resolved_at).
3. **Censura por la izquierda de las status pages:** los proveedores solo publican incidentes que ellos decidieron declarar. La tasa λ observada es la tasa de *incidentes declarados*, no de fallas reales. Se dice explícitamente.
4. **Features escasas para ML:** provider, impact, timestamps, componentes afectados, texto del título. No hay telemetría interna del proveedor.
5. **45 días de CI runs, 700 obs.** Los estados `skipped` y `action_required` no son fallas — la tasa de fallo real se calcula sobre runs ejecutados con verdict (success+failure = 518 → failure rate observada 16.2%, no 84/700).

---

## Las 5 notebooks

### NB01 — Descriptivo: ¿Cuánto error budget consumen mis dependencias y a qué ritmo?

**Pregunta real:** Si yo prometo a mis usuarios un SLO interno que depende de GitHub y Anthropic, ¿qué SLO puedo prometer de forma realista, dado el comportamiento observado de esos proveedores?

**Método:**
- Disponibilidad observada por proveedor: A = 1 − (Σ duration_min ponderada por impact) / ventana total
- Burn rate: consumo de un budget hipotético (99.9%, 99.5%, 99.0%) semana a semana, con las ventanas de 30 días rodantes
- Comparación de burn por proveedor y por severidad
- CI runs: failure rate real (sobre runs con verdict) por repo, como proxy de "carga de trabajo interna generada por CI roto"

**Decisión que informa:** qué SLO firmar hacia adentro. Si GitHub solo entrega ~99.5% observado en el periodo, prometer 99.9% end-to-end es matemáticamente imposible sin redundancia.

**Qué contaría como hallazgo real:** el SLO máximo prometible por proveedor y la sensibilidad de esa cifra a cómo se ponderan los incidentes `minor` (¿cuenta un minor de 6 horas como downtime completo?). El hallazgo es el *método de decisión*, no el número exacto.

**Anti-tautología:** los datos son observaciones externas de status pages reales; nadie plantó nada. El riesgo aquí no es tautología sino *sobregeneralización de 9 semanas* → se declara la ventana y no se extrapola a "GitHub es así siempre".

**Fixes de revisión (v1):**
- Las ventanas rodantes de 30 días sobre ~63 días de datos comparten >95% de datos entre puntos adyacentes — son pseudo-réplicas autocorrelacionadas, no muestras semanales independientes. La gráfica de burn rate debe declarar el solapamiento y no presentarse como "tendencia" con precisión independiente por punto.
- Toda gráfica de burn rate muestra explícitamente la ventana de 9 semanas; nada de suavizar hacia una tasa que aparente estabilidad.

---

### NB02 — Diagnóstico: ¿La variabilidad del TTR es ruido de proceso o tiene estructura?

**Pregunta real:** Cuando mi proveedor dice "resolvimos en 60 minutos como mediana", ¿qué me dice eso de lo que debo *presupuestar*? ¿La distribución del TTR justifica planear con la media, la mediana o un percentil alto?

**Método:**
- Ajuste distribucional del duration_min por proveedor: log-normal vs. exponencial vs. Weibull vs. gamma, comparadas por AIC + QQ-plots
- Test formal de log-normalidad (Shapiro-Wilk sobre ln(TTR))
- c²_s (CV² del tiempo de servicio) por proveedor — el insumo directo del factor V en VUT
- Brecha media/mediana: MTTR vs. mediana TTR, y qué implica para staffing (conectar a NB03)
- GESD sobre ln(TTR) para identificar los incidentes-outlier y examinarlos cualitativamente (¿qué tuvieron en común los 3-4 peores?)
- Estratificación por impact: ¿los critical son más largos o solo más severos?

**Decisión que informa:** con qué número planear capacidad. Si c²_s >> 1, el staffing basado en la media subestima sistemáticamente las colas (VUT).

**Qué contaría como hallazgo real:** el AIC puede elegir cualquiera de las 4 distribuciones — no está garantizado que gane log-normal. Si gana Weibull, eso se reporta y se discute (la teoría de Kline 1984 dice log-normal para *repair times* de sistemas multicomponente; una status page mide *detección+mitigación+comunicación*, que es otro proceso). El resultado honesto puede contradecir el prior teórico.

**Anti-tautología:** el test puede fallar. Ese es el punto.

**Fixes de revisión (v1):**
- **Pre-registro GESD:** r = 5 (máximo de outliers a probar), fijado aquí antes de ver los datos. No se ajusta post hoc.
- **Reglas de decisión AIC:** se reportan ΔAIC y pesos de Akaike, no un solo "ganador". Regla declarada de antemano: ΔAIC < 2 = distribuciones indistinguibles a este n. Con n≈50 por proveedor, log-normal/gamma/Weibull pueden empatar — el empate se reporta como empate.
- **Comparación critical vs. minor:** con n=15 critical / n=13 major, nada de t-tests. Mann-Whitney U + IC bootstrap sobre la diferencia de medianas, reportando el ancho del IC.

---

### NB03 — Predictivo (capacidad): ¿Cuántos ingenieros necesito en una semana crítica?

**Pregunta real:** En la peor semana observada del periodo (por conteo y severidad de incidentes), ¿cuántos ingenieros de guardia necesito para que el 90% de los incidentes empiece a atenderse en <30 min?

**Método:**
- λ empírica: incidentes/día del dataset real, con la semana pico identificada
- μ empírica: del ajuste de NB02 (mediana y media del TTR real)
- Erlang C como *piso teórico*: c mínimo para SL(30 min) ≥ 90% bajo supuestos M/M/c
- Corrección de supuestos explícita:
  - Test de sobredispersión de llegadas (var/media de conteos diarios) — si falla Poisson, se dice y se cuantifica el efecto direccional
  - c²_s de NB02 ≠ 1 → aproximación de Kingman multi-servidor (Allen-Cunneen) como segunda estimación
  - Comparación Erlang C vs. Allen-Cunneen: la brecha ES el hallazgo — "el modelo de libro de texto te diría c=2; la corrección por variabilidad real te dice c=3"
- Escenario sintético DORA como tercera columna: "un mundo DORA-mediano necesitaría X" (declarando λ=1.7/día del generador)

**Decisión que informa:** dimensionamiento del on-call. Google SRE dice mínimo 8 para 24/7 single-site; este análisis muestra el cálculo detrás de una recomendación así para una operación pequeña.

**Qué contaría como hallazgo real:** la magnitud de la corrección por variabilidad (Kingman) sobre el resultado de libro de texto. Si Erlang C y Allen-Cunneen coinciden, también es hallazgo (c²_s cercano a 1).

**Anti-tautología:** los inputs (λ, μ, c²_s) vienen de datos reales; el modelo es normativo (dice qué *deberías* tener, no qué hay). No hay resultado plantado posible.

**Riesgo conocido:** n pequeño hace λ de la semana pico frágil. Mitigación: intervalos por bootstrap sobre λ y μ, propagados al c recomendado (el resultado es "c=2–4", no "c=3").

**Fixes de revisión (v1):**
- **Sobredispersión confirmada empíricamente por el revisor:** var/media de conteos diarios = 1.83 → Poisson falla y la corrección Allen-Cunneen NO es opcional. GitHub TTR: media 200 min vs. mediana 96 min → c²_s claramente ≠ 1.
- **Bootstrap de λ_pico especificado:** la semana pico (semana 23, 20 incidentes) es un estadístico de orden extremo entre solo 9 semanas — un bootstrap iid ingenuo de sus 7 días subestima la incertidumbre. Unidad de remuestreo declarada: días agrupados por día-de-semana a través de las 9 semanas. Cross-check obligado: IC analítico de Poisson sobre el conteo de la semana 23. Se declara el riesgo de regresión a la media ("la peor semana observada" tiende a exagerar).
- **Visualización:** Erlang C y Allen-Cunneen comparten los mismos inputs (λ, μ) y solo difieren en el modelo — se grafican como "mismo mundo, dos correcciones", visualmente separados de la columna sintética DORA que es "otro mundo, parámetro declarado λ=1.7/día". Tres columnas iguales implicarían tres líneas de evidencia independientes, lo cual es falso.

---

### NB04 — Predictivo (severidad): ¿Puedo saber temprano si un incidente será largo?

**Pregunta real:** En el minuto 0 de un incidente (cuando el proveedor lo declara), ¿la información disponible en ese momento predice si será un incidente largo (>P75 de duración)?

**Método:**
- Target binario: duración > P75 (~2.4 h para GitHub) — definido sobre datos reales
- Features disponibles en t=0 SOLAMENTE: provider, impact declarado inicial, hora del día, día de semana, número de componentes afectados, longitud/keywords del título
- Regresión logística (no gradient boosting — n=100 no aguanta más) con validación cruzada estratificada
- Baseline obligado: predecir siempre la clase mayoritaria + predecir por impact solamente
- AUC con IC por bootstrap

**Decisión que informa:** política de escalación temprana — ¿vale la pena despertar al senior en el minuto 0, o el impact declarado ya contiene toda la señal?

**Qué contaría como hallazgo real:** **el resultado esperado honesto es un null o casi-null** (AUC 0.5–0.65). Con n=100 y features pobres, encontrar AUC 0.9 sería señal de leak, no de éxito. El hallazgo publicable: "el impact inicial declarado aporta X de señal; el resto del contexto casi nada — la política de escalación no puede ser más lista que la severidad declarada". Un null honesto con IC es mejor portfolio que un AUC inflado.

**Anti-tautología:** el riesgo real es leakage (usar información posterior a t=0), no plantado. Checklist de leakage explícito en la notebook.

**Fixes de revisión (v1) — esta notebook recibió los flags más serios:**
- **Leakage en `impact` (hallazgo del data-analyst):** el CSV es un snapshot único; las status pages escalan el impact durante el incidente (minor → major → critical). Lo capturado es casi seguramente el impact *final/asentado*, no la declaración del minuto 0 — y el impact final codifica parcialmente la duración. **Resolución:** la feature se reetiqueta como `settled_impact` y la pregunta se reformula honestamente: "¿cuánta de la 'predictibilidad' aparente proviene de que el impact final ya conoce el desenlace?" El modelo con settled_impact se presenta como *techo optimista* (upper bound con leakage declarado), y el modelo sin impact como la estimación honesta de t=0. La brecha entre ambos ES el hallazgo sobre el valor real del impact declarado.
- **EPV≈2–3 (hallazgo del data-scientist):** solo 25 positivos (duración > P75 = 143.5 min) sobre 99 casos. La lista de features dummy-codificada implica >10 parámetros → EPV muy por debajo del umbral de 10. **Resolución:** feature set capado a priori (no selección sobre los datos, que sería leakage): provider + settled_impact + hora binaria (horario laboral sí/no). Regresión logística con regularización L2. Nada de título/keywords ni conteo de componentes.
- **`affected_components` descartada como feature:** poblada 88% en Anthropic vs. 54% en GitHub — co-codifica prácticas de reporte del proveedor, no características del incidente.
- **Provider como señal dominante declarada:** GitHub 34% de incidentes "largos" vs. Anthropic 16% — se declara de antemano que provider (no impact) puede ser el predictor principal.
- **Claim de CV corregido:** stratified k-fold mide "generaliza a un split aleatorio de estas 9 semanas", NO "generaliza a incidentes futuros". La política de escalación necesita lo segundo; la notebook lo dice explícitamente.
- **Bootstrap AUC estratificado por clase:** con ~25 positivos, un bootstrap no estratificado produce remuestras degeneradas que inflan el IC.

---

### NB05 — Prescriptivo: ¿Qué hago cuando la cola se llena de tickets bloqueados por el proveedor?

**Pregunta real:** En una semana con sobrecarga de incidentes urgentes que dependen de un tercero (yo no puedo resolverlos, solo mitigarlos y esperar), ¿cuál es la política de triaje que minimiza el daño?

**Método:** análisis de política, no ML.
- Formalización: dos clases de trabajo — (a) resoluble internamente (μ propio), (b) bloqueado externamente (μ dictado por el proveedor, distribución de NB02)
- La semana crítica real del dataset como caso de estudio: reconstruir la línea de tiempo de la peor semana observada (¿cuántos incidentes simultáneos llegó a haber? ¿de qué proveedores?)
- Modelo de prioridades: cμ-rule (priorizar por costo×tasa de servicio) — para trabajo bloqueado externamente, μ efectivo ≈ 0 mientras el proveedor no resuelva → la regla dice: NO asignar ingenieros a esperar; asignarlos a mitigación de impacto y comunicación, que sí tienen μ > 0
- Simulación simple de la semana pico bajo 3 políticas: FIFO, prioridad por severidad, cμ-rule — comparar tiempo total de daño (área bajo la curva de tickets abiertos ponderados por severidad)
- Error budget de NB01 como criterio de activación: burn rate > umbral → modo degradado formal (statuspage propia, comunicación proactiva, pausar deploys)

**Decisión que informa:** el runbook de sobrecarga — qué hace cada ingeniero cuando hay 4 incidentes críticos simultáneos y 2 personas de guardia.

**Qué contaría como hallazgo real:** la diferencia cuantificada entre políticas en la semana real reconstruida. Si FIFO y cμ empatan (posible con n chico), se reporta el empate y se explica en qué condiciones divergirían.

**Anti-tautología:** la simulación usa la traza real de la semana pico, no una traza generada para que gane una política.

**Fixes de revisión (v1):**
- **La semana pico real es más suave que el escenario ilustrativo:** semana 23 = 20 incidentes, pero solo 1 critical y 3 major (el resto minor). El escenario "4 críticos simultáneos con 2 de guardia" NO ocurrió — se mantiene como *stress test hipotético claramente etiquetado*, separado de la reconstrucción de la semana real observada. Dos secciones distintas: (a) replay de la semana real, (b) stress test sintético declarado.
- **Robustez de la comparación de políticas:** un ranking determinista sobre una sola traza de ~20 eventos no es generalizable. Chequeo comprometido: se remuestrean los tiempos de servicio por incidente desde las distribuciones ajustadas en NB02 (manteniendo la secuencia de llegadas real fija) × 1,000 réplicas, y se reporta *en qué fracción de réplicas gana cada política*. "cμ gana en 78% de las réplicas" es defendible; "cμ ganó" a secas no.
- **Etiquetado de alcance:** la comparación es un caso de estudio de una semana, no una recomendación de política con respaldo estadístico general. La gráfica lo dice.

---

## Estructura común de cada notebook

1. **La pregunta** (una oración, antes de cualquier dato)
2. **Por qué esta pregunta importa** (la decisión que informa)
3. **Los datos y sus límites** (incluye la nota de censura de status pages)
4. **El método y sus supuestos** — con los tests de supuestos EJECUTADOS, no mencionados
5. **Resultado** — con incertidumbre (IC bootstrap donde aplique)
6. **Qué haría distinto un decisor** después de leer esto
7. **Qué NO se puede concluir** de estos datos

## Mapa a fundamentos científicos

| NB | Herramientas | Sección de scientific_foundations |
|---|---|---|
| 01 | Error budget, disponibilidad, renewal process | Herramienta 6 |
| 02 | Log-normal, GESD, c²_s | Herramientas 2, 3 |
| 03 | Erlang C, Kingman/Allen-Cunneen, VUT | Herramientas 4, marco VUT |
| 04 | Regresión logística, evaluación honesta | (nueva — estándares de evaluación de data-scientist) |
| 05 | cμ-rule, prioridades en colas, error budget como trigger | Herramientas 4, 6 |

SPC y SARIMA **salen del stack**: SPC requiere series de telemetría continua que ya no tenemos (era del dataset sintético viejo); SARIMA con 9 semanas de datos diarios no tiene ciclos suficientes para estimar estacionalidad de forma defendible. Se mencionan en el MDX como "qué usaríamos con 6+ meses de datos" — es más honesto que forzarlas.

## Qué pasa con las notebooks viejas

**DECISIÓN DE MARIO (2026-07-03): borrarlas — no aportan nada.** Alcance del borrado: las 5 notebooks viejas, los 3 CSVs sintéticos viejos (pulse_telemetry, support_tickets, migration_cohorts), `src/data_generator.py` (solo genera esos 3 CSVs), `src/anomaly.py` + `src/api_integration.py` (solo sirven a las notebooks viejas 02/05) y sus tests. Los CSVs sintéticos NUEVOS (synthetic_ci_runs, synthetic_incidents) se conservan — son el baseline DORA del diseño actual.

---

## Log de revisión (v1, 2026-06-30)

Revisado en paralelo por dos agentes con roles sin solapamiento, antes de escribir código:

**data-analyst (framing):** persona coherente en las 5; las 5 preguntas PASS como reales; anti-tautología del sintético PASS. Flags incorporados: leakage de `settled_impact` en NB04 (el hallazgo más importante de la revisión), asimetría de `affected_components` por proveedor, falsa estabilidad visual del burn rate (NB01), tres-columnas-tres-evidencias en NB03, y semana pico como anécdota vs. resultado general en NB05.

**data-scientist (metodología):** verificó empíricamente contra los CSVs — var/media=1.83 (sobredispersión real), P75 combinado=143.5 min, 25 positivos para NB04, semana pico=20 incidentes (1 critical/3 major). Confirmó que sacar SPC y SARIMA está estadísticamente justificado, no es conservadurismo (SARIMA sobre 66 días de conteos sobredispersos con 9 ciclos no pasaría Ljung-Box con potencia real). Fixes incorporados: EPV y feature cap en NB04, bootstrap de valor extremo en NB03, pre-registro GESD r=5 y ΔAIC en NB02, perturbación ×1,000 en NB05, pseudo-réplicas de ventana rodante en NB01.

**Verificado (2026-07-04):** `impact` ES el estado final/asentado, por construcción de la captura — el endpoint Statuspage v2 (`/api/v2/incidents.json`) devuelve el impact vigente al momento del fetch, y para incidentes ya resueltos eso es el valor final, nunca la declaración del minuto 0 (un snapshot único no puede recuperarla). El diseño de NB04 con `settled_impact` como techo optimista se mantiene tal cual. Documentado en `notebooks/data/real/README.md` y en el docstring de `src/capture_status_pages.py`.
