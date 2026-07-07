# Plan de revival — `real_estate` (King County House Prices)

> Documento interno de diseño/investigación para Mario. Español por convención.
> Producido por `thinker-realestate` para la tarea **T-115**. Lo implementa **T-116**.
> Ámbito: diagnóstico + plan concreto de mejora. **No** toca código (tarea de thinker).

Directiva de Mario (parafraseada): *"inclúyelo, amplíalo, modifícalo, púlelo otra vez — la
idea núcleo cruda es muy buena, pero lo he mantenido mal con los años."*

---

## 0. TL;DR (lo que T-116 tiene que lograr)

El proyecto está **conceptualmente roto en su raíz por una tautología**: los datos son
sintéticos y el generador *planta* la estructura que luego el notebook "descubre" (una
superficie geográfica gaussiana no-aditiva que sólo los árboles boosteados pueden capturar).
La conclusión "GradientBoosting gana" está horneada en `data_generator.py`. Eso viola la regla
permanente del workspace: *si los datos se diseñaron para que el análisis tenga éxito, es una
tautología, no un hallazgo.*

El notebook, para su crédito, **ya es honesto sobre esto** (la última celda lo admite
explícitamente). Pero la honestidad no arregla el defecto: un análisis cuya única conclusión
válida es "el método funciona sobre datos que yo fabriqué" no responde una pregunta real.

**La jugada central del revival:** migrar al **dataset REAL de King County** (público, ~21.613
ventas, 2014–2015 — el original que el generador imita) y convertir la *suposición plantada*
en una **hipótesis falsable sobre datos reales**. El set sintético **sobrevive, pero degradado
a benchmark declarado**: sirve para validar que el pipeline recupera una superficie espacial
*conocida* (con sus parámetros de generación declarados al lado de la comparación), y nada más.

Ámbito de página del sitio: **FUERA de este epic** (ver §7). Primero se arregla el proyecto.

---

## 1. Estado actual (lo que se leyó, en su totalidad)

Ubicación: `Portfolio-repo/_pendiente_decision/real_estate/` (trabajo "aparcado").

```
README.md                         # narrativa del proyecto (genérica, rutas obsoletas)
LICENSE                           # MIT
pyproject.toml                    # deps + config ruff/mypy/pytest
data/
  kc_house_data_synthetic.csv     # 5.000 filas, 22 cols (SINTÉTICO, committeado)
  README.md                       # diccionario de columnas
src/
  __init__.py
  data_generator.py               # el generador sintético (seed 42)
notebooks/
  house_sales_king_county.ipynb   # ÚNICO notebook: 6 secciones + "what explains the win"
tests/
  conftest.py                     # inserta src/ en el path
  unit/test_data_generator.py     # 1 smoke test (importable) — nada más
```

Lo que **funciona bien** y hay que **conservar**:
- El generador es técnicamente competente y *auto-consciente* (comentarios explican el DGP).
- El notebook técnicamente corre y la última celda es un ejemplo raro de honestidad analítica
  (distingue "el método" de "un hallazgo real", ya en algo cercano a la voz de Mario).
- Feature engineering razonable (`age`, `has_basement`, `has_renovation`, `log_price`).
- Comparación de 4 modelos con métrica back-transformada a USD (interpretable).
- Infra de proyecto decente (pyproject, ruff, mypy, marcadores pytest).

---

## 2. Diagnóstico — qué está obsoleto / roto

### 2.1 Defecto conceptual (bloqueante) — la tautología
- `data_generator.py` construye el precio como `sqft*150 + (grade-7)*... + interacción
  grade×sqft + suma de gaussianas espaciales (hotspots Bellevue/Seattle/Sammamish) + ruido
  lognormal`. El notebook luego "encuentra" que GB gana porque captura esa superficie espacial.
  **La respuesta está en el generador.** El ranking de modelos es un artefacto del diseño.
- Consecuencia: la pregunta actual ("¿qué clase de modelo captura el proceso generador y qué
  features llevan la señal?") es **incontestable de forma honesta con estos datos**. Sobre un
  DGP conocido, la única verdad es "cada modelo recupera exactamente lo que su clase de
  hipótesis permite" — cierto por construcción, informativo de nada sobre el mundo.

### 2.2 Problemas metodológicos (aplican también a datos reales)
1. **Split único 80/20, sin validación cruzada.** Los R² no tienen incertidumbre. Un solo
   `random_state=42` puede ser afortunado. Falta k-fold repetido con barras de error.
2. **Fuga de datos en la imputación.** `bedrooms/bathrooms` se imputan con la media del
   dataset *completo* antes del split → el test contamina el entrenamiento. Debe hacerse
   *dentro* del `Pipeline`/CV (`SimpleImputer` en el pipeline).
3. **Colinealidad estructural.** `sqft_above + sqft_basement = sqft_living` (exacto por
   construcción; casi exacto en datos reales). Meter las tres como features rompe la
   interpretabilidad de coeficientes lineales. Elegir subconjunto o documentar.
4. **Sin validación cruzada espacial.** Casas vecinas correlacionan (y hay features de
   vecindario `sqft_living15/lot15`). Un split aleatorio filtra vecinos entre train/test →
   R² optimista. Considerar bloqueo por zipcode / spatial CV.
5. **Sin baseline honesto.** No hay un "predecir la media" ni "mediana por zipcode" contra el
   que contextualizar el R². Sin baseline, 0.78 no significa nada.
6. **Sin tuning declarado.** Hiperparámetros (`n_estimators=300, max_depth=...`) son
   arbitrarios y no validados. O se tunean por CV o se declara que son defaults sin tunear.
7. **Sin tests de supuestos EJECUTADOS.** El notebook afirma que los residuos se ensanchan en
   la cola alta pero no corre un test (heterocedasticidad, normalidad de residuos,
   autocorrelación espacial p.ej. Moran's I). El estándar del workspace (proyecto cloud) es
   *ejecutar* los tests de supuestos, no describirlos.

### 2.3 Obsolescencia / bit-rot (pulido)
- **README rutas rotas:** `cd Portfolio/real_estate` (ahora vive en `_pendiente_decision/`);
  `git clone ...Portfolio.git` desactualizado.
- **README manda `pytest -m unit`** pero pytest **no está instalado en el venv compartido**
  (política del workspace). Alinear instrucciones con la realidad (o instalar pytest vía uv,
  decisión de Mario).
- **Dependencia muerta:** `structlog` está en `pyproject.toml` pero nadie lo usa.
- **Tests vacíos:** un único smoke test de importabilidad. No prueban nada del generador ni
  del pipeline.
- **Estilo de plots:** `plt.style.use('dark_background')` + paletas ad-hoc — sin alinear con
  el design system Mitteleuropeo del sitio (a decidir según destino, ver §7).
- **Voz de prosa:** el README suena a relleno IA genérico ("Iris of real estate", tabla de
  stack decorativa). El notebook está mejor pero no pasó la campaña de restyle del 2026-07-04
  (estaba aparcado). Necesita pasar por el `prose-stylist` con la guía de voz de Mario.
- **`data_generator.py`** tiene `output_dir="../data"` como default: correr `python
  src/data_generator.py` desde la raíz escribe *fuera* del proyecto. Path frágil.
- **Estructura delgada:** un solo notebook, 6 secciones sueltas, frente a la estructura
  pre-registrada de 7 secciones de los proyectos profesionales.

---

## 3. La pregunta honesta que el proyecto debe responder

**Regla:** sin tautología. Los datos no pueden estar diseñados para que el análisis triunfe.

### Pregunta propuesta (sobre datos REALES de King County)

> **"En el mercado real de King County, ¿cuánta capacidad predictiva adicional compra
> realmente modelar la estructura de ubicación no-aditiva por encima de un baseline aditivo
> bien especificado — y dónde se equivoca sistemáticamente el modelo (¿es error geográfico o
> error de cola de lujo)?"**

Por qué es honesta y no-tautológica:
- Nadie sabe *a priori* cuánto lift da la no-aditividad espacial en el mercado real. El
  resultado puede ser grande, pequeño o nulo — cualquiera es publicable. Un **null honesto**
  ("la ubicación no aporta lift más allá de lo aditivo") es un hallazgo válido.
- Es **decision-relevant**: un tasador/prestamista actúa distinto si sabe *dónde* falla el
  modelo (¿barrios concretos? ¿tramo de lujo?) que si sólo ve un R² global.
- Convierte la *suposición plantada* del generador en una *hipótesis testeada*: exactamente lo
  que la última celda actual dice que haría "si apuntara a datos reales mañana".

### Rol del set sintético — **benchmark declarado** (única función permitida)
- Se conserva `data_generator.py` como **validación de recuperabilidad**: "sobre datos donde
  YO planté una superficie espacial (hotspots en `[(47.62,-122.21,220k),
  (47.63,-122.35,150k), (47.57,-122.04,90k)]`, σ²=0.012, ruido lognormal σ=0.25, seed 42),
  el pipeline recupera +X R² con GB sobre el baseline lineal."
- **Los parámetros del generador se declaran explícitamente junto a la comparación** (regla del
  workspace). El sintético NUNCA se presenta como evidencia sobre el mercado; sólo como prueba
  de que el instrumento (el pipeline) puede recuperar una señal *conocida*.
- Contraste final: "El benchmark sintético muestra que el método *puede* detectar una
  superficie espacial si existe (+X R²). En datos reales el lift observado es +Y R². Si Y ≪ X,
  el mercado real de King County no tiene la estructura espacial fuerte que planté; si Y ≈ X,
  sí la tiene." Eso es un hallazgo real, falsable, y usa el sintético de forma legítima.

---

## 4. Ampliar / Modificar / Pulir — plan concreto para T-116

### 4.1 DATOS — obtener King County real (prioridad 1)
- **Adquirir el dataset real** `kc_house_data.csv` (canónico: ~21.613 filas, 21 columnas, ventas
  May-2014 a May-2015, King County WA). Fuente original: Kaggle `harlfoxem/housesalesprediction`
  (licencia CC0 / registros públicos del condado). Kaggle requiere auth; si no hay credenciales,
  usar un mirror público estable (raw de GitHub) — **T-116 debe registrar la URL/fuente exacta y
  un checksum** en `data/README.md` para provenance.
- Guardar como `data/real/kc_house_data.csv`. Mover el sintético a
  `data/synthetic/kc_house_data_synthetic.csv` (espeja la convención `real/` vs `synthetic/`
  del proyecto cloud). Actualizar rutas del notebook y del generador.
- **Reescribir `data/README.md`**: describir explícitamente (a) datos reales = fuente de verdad,
  con provenance + licencia + checksum + gotchas conocidos del dataset (p.ej. `bedrooms=33`
  outlier famoso, `sqft_lot` con outliers, precios truncados); (b) sintético = benchmark
  declarado con TODOS los parámetros del generador listados.
- Nota de provenance para el `data-engineer`: verificar que las columnas del real casan con las
  que el notebook espera; el real NO tiene `Unnamed: 0` inyectado ni los NaN sintéticos — el
  wrangling de NaN habrá que replantearlo (el real tiene sus propias imperfecciones reales).

### 4.2 MODIFICAR — corregir métodos
1. Reemplazar split único por **k-fold repetido (o CV anidada si hay tuning)** con media ± sd de
   R²/MAE/RMSE. Reportar incertidumbre, no puntos.
2. Mover **toda** transformación dependiente de datos (imputación, scaling, poly) **dentro del
   `Pipeline`** para eliminar fuga en CV.
3. Añadir **baselines honestos**: DummyRegressor (media) y mediana-por-zipcode. Contextualizar
   todo R² contra ellos.
4. **CV espacial / bloqueo por zipcode** (al menos como robustez): mostrar cuánto cae el R² sin
   fuga de vecinos. Este es el corazón de la pregunta de §3.
5. Resolver la **colinealidad** `sqft_above+basement=living`: elegir features y justificar; para
   el modelo lineal, reportar VIF.
6. **Tests de supuestos EJECUTADOS**: normalidad/heterocedasticidad de residuos (p.ej.
   Breusch-Pagan / gráfico + estadístico), y **autocorrelación espacial de residuos (Moran's I)**
   — este último es directamente la evidencia de si la ubicación lleva señal no capturada.
7. Tuning declarado: o `GridSearchCV`/`RandomizedSearchCV` con la grilla registrada, o una nota
   explícita "defaults sin tunear" (no pretender lo que no se hizo).

### 4.3 AMPLIAR — profundidad analítica y features
- **Análisis de error por segmento**: descomponer el error por zipcode/tramo de precio.
  Responder "¿dónde falla?" con mapas de residuos, no sólo un scatter global.
- **Features geoespaciales reales**: distancia a downtown Seattle (CBD), distancia a costa/agua,
  target-encoding de zipcode *fold-safe* (dentro del CV para no filtrar), densidad local. Éstas
  son la forma legítima de "dar al modelo la ubicación" y medir su lift → conecta con la pregunta.
- **Importancia honesta**: reemplazar/complementar impurity importance (sesgada hacia
  alta-cardinalidad) con **permutation importance** en test, o SHAP si se quiere profundidad.
- **Adoptar la estructura de 7 secciones** del proyecto cloud, adaptada:
  1) pregunta → 2) por qué importa (decisión del tasador/prestamista) → 3) los datos y sus
  límites (provenance real, gotchas, qué NO es comparable) → 4) método con **tests de supuestos
  ejecutados** → 5) resultado con incertidumbre (CV ± sd, no punto) → 6) decisión (qué haría un
  tasador con esto) → 7) qué esto NO puede decir (extrapolación temporal 2014-15, fuera de KC,
  cola de lujo, mercados no estacionarios).
- Considerar **partir en 2 notebooks** si crece demasiado: `01_price_model.ipynb`
  (baseline→ensembles, la pregunta central) + `02_geographic_signal.ipynb` (superficie espacial,
  Moran's I, benchmark sintético vs real). Decisión de T-116 según longitud; no forzar si un
  notebook bien estructurado alcanza (regla: sin cortes de alcance prematuros, pero tampoco
  gold-plating).

### 4.4 PULIR
- **Prosa en voz de Mario**: pasar README + celdas markdown del notebook por el agente
  `prose-stylist` con la guía `.../cloud_infrastructure_support/research/prose_propuesta.md`.
  La última celda ("what explains the win") ya está cerca — usarla de referencia de tono.
- Arreglar **rutas del README** (ubicación real, clone correcto) y la instrucción de **pytest**
  (o instalar pytest en el venv vía uv si Mario lo aprueba, o quitar la línea).
- Quitar dependencia muerta `structlog` de `pyproject.toml` (o usarla de verdad para logging del
  generador — preferible quitarla, no es un proyecto de instrumentación).
- Arreglar el default frágil `output_dir` del generador (usar ruta relativa al archivo, no al CWD).
- **Tests reales**: propiedades del generador (shapes, rangos, seed determinista, % de NaN) y un
  smoke test del pipeline (entrena y produce R² finito). Sólo si Mario aprueba pytest en venv;
  si no, dejar los tests como están y no prometerlos en el README.
- Estilo de plots: alinear con el design system **sólo si** el destino lo requiere (ver §7); por
  ahora mantener consistencia interna limpia.

### 4.5 Notebooks — proceso de revisión (obligatorio, no auto-certificar)
Cuando T-116 tenga diseño y notebook: correr el loop de revisores del workspace
(`data-analyst` framing/tautología · `data-engineer` provenance del real · `data-scientist`
validez estadística · `qa-engineer` reproducibilidad) y un ciclo de fixes, como manda CLAUDE.md.
La revisión de *diseño* (¿la pregunta de §3 sobrevive?) debe pasar **antes** de escribir código.

---

## 5. Riesgos y decisiones abiertas para Mario

1. **Adquisición de datos reales:** ¿hay credenciales de Kaggle, o T-116 usa un mirror público?
   (Bloquea el paso 1. Recomendación: mirror público con checksum documentado si no hay Kaggle.)
2. **pytest en el venv compartido:** actualmente ausente por política. ¿Instalar vía uv para
   tener tests reales, o mantener el proyecto sin suite y limpiar el README? (Decisión de Mario.)
3. **Ubicación final del proyecto** (Mario dijo "inclúyelo" → sale de `_pendiente_decision/`):
   encaja tanto en `01_professional/` (pipeline ML aplicado, clásico y hireable) como podría
   argumentarse en `02_intellectual/`. **CLAUDE.md prohíbe mover entre tracks sin preguntar.**
   Presentar ambas opciones a Mario; no decidirlo dentro de T-116 sin su OK. (El resto del
   revival no depende de dónde acabe; se puede hacer in-place en `_pendiente_decision/` y mover
   al final.)
4. **¿Un notebook o dos?** (§4.3) — dejar a criterio de T-116 según longitud tras el rediseño.

---

## 6. Criterio de "hecho" para el revival (para T-117 / verifier)

- [ ] Datos reales de King County presentes con provenance documentada (fuente + licencia +
      checksum) en `data/README.md`; sintético degradado a `data/synthetic/` con parámetros del
      generador declarados.
- [ ] El notebook responde la pregunta de §3 sobre datos REALES; ninguna conclusión depende de
      estructura plantada. El sintético aparece sólo como benchmark declarado con contraste
      explícito real-vs-sintético.
- [ ] Métodos corregidos: CV con incertidumbre, imputación sin fuga, baselines, tests de
      supuestos ejecutados (incl. Moran's I sobre residuos), colinealidad tratada.
- [ ] Estructura de 7 secciones; prosa pasada por `prose-stylist` (voz de Mario).
- [ ] README/pyproject/data-README sin rutas rotas, sin deps muertas, instrucciones alineadas
      con la realidad del venv.
- [ ] Loop de revisores (analyst/engineer/scientist/qa) pasado con fixes aplicados.
- [ ] Nada committeado/pusheado salvo que Mario lo pida (regla permanente).

---

## 7. Página del sitio (case-study) — **FUERA de alcance de este epic**

Recomendación explícita y por defecto: **autorar la página del sitio (una `real_estate.mdx` +
flip de `published` en `site/src/lib/studies.ts`) es un paso POSTERIOR y SEPARADO, no parte de
este epic (T-115/T-116/T-117).**

Razones:
- Este epic arregla el **proyecto subyacente** primero. Publicar un case-study sobre un análisis
  todavía tautológico sería propagar el defecto al escaparate.
- Precedente del workspace: `hci-support.mdx` **se mantiene sin publicar hasta que Mario escribe
  el argumento él mismo**. La misma disciplina aplica aquí: la página la escribe Mario (o un epic
  aparte) una vez que el proyecto tiene un hallazgo real y estable.
- Separar mantiene el epic acotado y verificable: "¿el proyecto responde una pregunta honesta con
  datos reales?" es un gate limpio; "¿además está bien la prosa MDX del sitio?" es otro trabajo.

Cuando llegue ese paso separado, sus insumos serán: el hallazgo estable de §3, la estructura de
7 secciones ya escrita, y la decisión de ubicación (§5.3). No antes.
