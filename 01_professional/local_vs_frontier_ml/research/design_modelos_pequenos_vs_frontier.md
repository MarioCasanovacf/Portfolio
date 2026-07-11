# Design doc — Applied ML to Business: cuándo poseer un modelo en vez de rentar la frontera

**Estado:** borrador v0.1 para revisión de agentes (`data-analyst` + `data-scientist`) antes de escribir código.
**Slot en el sitio:** `ml-second` (reservado en `studies.ts`, track `industry`, domain "Applied machine learning").
**Artefacto:** una **notebook `.ipynb`** (ver §6 — requisito duro de Mario).
**Idioma:** notebook/página en inglés; este doc en español.

---

## 1. La tesis (fijada por Mario, no la toca el agente)

> El modelo de frontera es la herramienta con la que se construye la solución **junto al ingeniero**. Su lugar es el desarrollo (etiquetar, generar, adjudicar, bajo auditoría) y el artefacto que queda desplegado es un modelo pequeño, propio y local. Saber repartir esos dos trabajos es lo que este case study documenta, y el patrón sirve mucho más allá del sentiment, **puesto que su fin es Applied Machine Learning to Business.**

El benchmark **no es la tesis; es la evidencia** de las razones por las que el artefacto desplegado debe ser el modelo propio. El frontier queda donde sí rinde: acelerando la construcción.

## 2. La pregunta real (y por qué NO es tautología)

Pregunta: *Para una tarea de clasificación de texto de alto volumen, bien definida, ¿dónde le gana de verdad un modelo especializado entrenado y corrido en local al reflejo de llamar a una API de frontera — en costo, latencia y privacidad — y cuánta accuracy cede, si es que cede alguna? ¿Y dónde sí conviene el frontier?*

Riesgo de tautología (la regla dura del portafolio): "los modelos chicos son más baratos" **afirmado** es marketing. Sólo cuenta si se **mide**. El diseño se blinda así:
- El lado local se **mide** (throughput, accuracy, costo marginal) en datos públicos, con código reproducible.
- El lado frontier se **coteja** contra benchmarks independientes públicos (no lo corremos: cero gasto en APIs — instrucción de Mario).
- Se declara **por adelantado** (§5) qué contaría como que el modelo chico *pierde*. Si a volumen bajo el costo total de ingeniería favorece a la API, se reporta como null honesto, no se esconde.

## 3. Datos

**Multilingual Amazon Reviews Corpus** (público, redistribuible, multilingüe → rima con la historia de +20 idiomas del sentiment work). Ventaja clave frente al trabajo de la empresa: **este case study puede publicar código Y datos** — es 100% reproducible, sin NDA ni ToS de por medio. (Alternativa más simple si el multilingüe da problemas de disponibilidad: *Amazon Polarity*. Decidir en la revisión.)

Nada del dato propietario de la empresa entra aquí. El sentiment work se cita como el **caso concreto** que motivó el patrón, no como fuente de datos.

## 4. Diseño del benchmark

### 4.1 Lado local — lo medimos nosotros
Entrenar/afinar un modelo pequeño (XLM-RoBERTa base o un destilado tipo distil-multilingual) sobre el dataset público, en la Mac de Mario. Métricas:
- **Accuracy / macro-F1** en un test congelado.
- **Throughput**: reviews/segundo en inferencia local (CPU/MPS), y tiempo de una corrida batch del corpus completo.
- **Costo marginal**: ~0 (sólo electricidad/amortización). Declarar el costo *único* de entrenamiento (local, sin GPU-hours rentadas).
- **Determinismo**: mismo input → mismo output, verificado.
- **Privacidad**: el dato nunca sale de la máquina (propiedad estructural, no medida).

### 4.2 Lado frontier — lo cotejamos, no lo corremos
Números de fuentes independientes públicas, citados con fecha:
- **Artificial Analysis** (`artificialanalysis.ai`) — precio $/1M tokens (in/out), time-to-first-token, tokens/seg, intelligence index, por modelo y proveedor.
- **LMArena / Chatbot Arena** — Elo de preferencia humana como proxy de calidad general.
- **Páginas de precios de proveedores** como ground-truth puntual.

De ahí se estima el **costo y la latencia de hacer el mismo trabajo con la API**: $ por cada 1000 (o 1M) reviews a precios de lista, y ms/request. Se modela el escenario de volumen del case study (cientos de miles de reviews, recurrente).

### 4.3 Ejes de comparación (las figuras)
- Accuracy vs **costo** (a volumen realista, recurrente).
- Accuracy vs **latencia/throughput**.
- **Privacidad / determinismo / control** — cualitativo pero fundamentado (dato no sale; frontera de decisión —umbral τ, rúbrica— es tuya y auditable; el modelo no cambia debajo de ti cuando el proveedor lanza otra versión).

### 4.4 El rol del frontier en el DESARROLLO (la columna de la tesis)
La sección central no es "chico gana": es que el frontier hace el **andamiaje de construcción** — etiquetar reviews ambiguas, generar ejemplos sintéticos de la clase minoritaria, adjudicar casos frontera — **bajo auditoría κ ciega**, junto al ingeniero, y lo que se despliega es el modelo chico entrenado con esas etiquetas. Se referencia el sentiment work como el caso donde esto ocurrió de verdad (el "LLM as a labeler like any other", κ 0.472→0.688). El frontier **no** se usa en inferencia de producción.

## 5. Reglas pre-registradas (anti-tautología — declarar ANTES de correr)

1. El test set local se congela antes de mirar resultados; un solo reporte final.
2. Se declara el umbral de "pérdida": si la accuracy local queda >X puntos por debajo de la referencia frontier comparable **o** si a volumen bajo (< N reviews/mes) el costo total (incl. tiempo de ingeniero para entrenar) favorece a la API, se reporta como tal.
3. La comparación de accuracy **no es cabeza-a-cabeza** salvo que exista un número publicado frontier sobre una tarea comparable; si no, se enmarca explícitamente como "el modelo chico alcanza X medido; la referencia frontier ronda Y según literatura/benchmark, en tarea análoga, no idéntica". Nada de inventar una derrota del frontier que no medimos.
4. Se nombra dónde el frontier legítimamente gana: arranque sin labels, volumen chico, tareas que piden razonar/generar. (Honest nulls > resultados inflados.)

## 6. Artefacto: NOTEBOOK, no código de agentes (requisito duro de Mario)

El análisis vive como **`.ipynb`**, no como scripts de agentes ni skills de subagentes ("no te va a servir a ti ni a nadie"). Concretamente:
- Ubicación: **carpeta NUEVA y pública `01_professional/<nombre>/`** (p. ej. `01_professional/local_vs_frontier_ml/`), con `notebooks/`, `data/` (muestra pública) y `README.md`, en la convención del resto de proyectos. **CRÍTICO: NO puede vivir dentro de `review_sentiment_ml/`, que está gitignorado por NDA — ahí la notebook nunca sería pública, y todo el punto de este case study es que SÍ lo sea (código + datos publicables).** Queda cotejable con `subscription_economics/*.ipynb`, `real_estate/house_sales_king_county.ipynb`, `cloud_infrastructure_support/04_incident_duration_prediction.ipynb`. El sentiment work (privado) sólo se **cita** como el caso motivador; no se importa nada de él.
- Ejecutable con el venv compartido (`Portfolio-repo/.venv/bin/python`, kernel `portfolio`), corrido desde su propio directorio.
- Misma **estructura de 7 secciones** y **voz** que las demás notebooks (guía `cloud_infrastructure_support/research/prose_propuesta.md`, 15 reglas; primera persona metodológica, sin retórica barata, cifras legibles por la Regla 14).
- Figuras reproducibles desde el notebook (matplotlib), no pegadas.
- El harness/agentes pueden *ayudar a construirla*, pero el entregable es la notebook limpia y corrible, con outputs ejecutados.

**Nota de coherencia (para Mario):** el sentiment work quedó como scripts `.py` por herencia de la migración del repo privado — no matchea la convención de notebooks del resto. Esta notebook de benchmark es la primera pieza de ese proyecto en formato notebook. Pregunta abierta para después: ¿quieres que eventualmente el sentiment work también se notebook-ifique para uniformar, o lo dejamos como scripts + esta notebook encima?

## 7. Qué NO puede decir (límites, sección honesta del notebook)

- Los números frontier son **estimados públicos con fecha**, no corridas nuestras; el precio y la latencia cambian rápido.
- La accuracy del frontier viene de benchmarks generales, **no de nuestra tarea exacta**; se declara la brecha.
- La ventaja de privacidad es estructural, no un número; se argumenta, no se mide.
- El resultado es sobre **esta clase de tarea** (alto volumen, bien definida, sensible a latencia/privacidad), no una condena general de las APIs.

## 8. Flujo

Design doc (este) → revisión `data-analyst` (¿pregunta real, no tautología?) + `data-scientist` (¿el benchmark es válido, las comparaciones honestas?) → construir la notebook → revisión `qa-engineer` + `data-scientist` con fix loop → Mario juzga → página MDX en el slot `ml-second` + `published: true`. Sin commits ni push salvo que Mario lo pida.
