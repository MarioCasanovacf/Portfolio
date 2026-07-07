# Fix spec — ingestión legislativa vs. el endpoint SITL en vivo

**Tarea:** T-106 (thinker). **Autor:** thinker-legislative. **Fecha:** 2026-07-05.
**Implementa:** T-107 (worker). **Alcance:** documento de diagnóstico + especificación de arreglo. NO se editó código fuente.

> **Cómo leer este documento.** La premisa de la tarea ("la ingestión real está rota:
> paths 404 de dipMex, columnas desalineadas, sin votos para 64-66") describe el estado
> **previo** registrado en la MEMORY de Mario. Al leer el código y los datos en disco
> encontré que **la mayor parte ya está arreglada**: existe un capturador SITL en vivo
> (`src/capture/sitl.py`) que implementa correctamente el endpoint verificado, la LXVI
> está capturada y cruzada contra las tallies oficiales, y `dbt build` corre en verde
> (ADR 004). La rotura que **queda** es distinta de la que describe la premisa, y este
> spec la aísla con precisión. Honestidad ante todo: no invento una rotura que ya no
> existe.

---

## 0. TL;DR (qué debe hacer T-107)

1. **El camino canónico ya funciona y NO se toca su lógica**: `scripts/ingest_dipmex.py`
   → `src/capture/sitl.py` → `scripts/ingest_sitl.py` → `dbt build`. Es el que produce
   los 798.445 votos atribuidos (dipMex 60+61 + SITL 66).
2. **La rotura viva es la capa de orquestación legacy**, desacoplada del camino canónico
   y que sí falla contra el endpoint: `flows/legislative_pipeline.py`, `src/capture/cli.py`,
   `src/capture/diputados.py` (`DiputadosScraper`) y la parte de-solo-descarga de
   `src/capture/dipmex.py`. Apuntan a URLs equivocadas, a nombres de tabla inexistentes
   y a transforms SQL obsoletos. Hay que **reconectarla al camino real o retirarla**.
3. **Hueco de cobertura real**: solo la **LXVI (66)** tiene votos por diputado
   capturados. La **LXIV (64)** y la **LXV (65)** NO están capturadas, aunque el scraper
   las soporta. Cerrar el hueco = correr `SitlScraper(64)` y `SitlScraper(65)` desde una
   red que resuelva el host gubernamental, con UA de navegador.
4. Alinear la documentación (README, comentarios de `sources` en dbt) que dice
   "legs 64-66" cuando en disco solo existe la 66.

---

## 1. Arquitectura real (dos pipelines, no uno)

En el repo conviven **dos** cadenas de ingestión. Es la fuente de toda la confusión.

### 1.A — Camino CANÓNICO (funciona; es el de los ADR 003/004 y el README)

```
dipMex (GitHub, legs 60-61 votos + 64/65/66 solo padrón)
   scripts/ingest_dipmex.py  --> raw.raw_dipmex_roster / _vote_events / _rollcall / _roster_recent

SITL en vivo (legs 64-66, voto por diputado)
   src/capture/sitl.py  --> data/raw/sitl/{slug}/sitl_votes_*.csv, sitl_vote_meta_*.csv, sitl_tallies_*.csv
   scripts/ingest_sitl.py  --> raw.raw_sitl_votes / _sitl_vote_meta / _sitl_tallies

dbt (dbt_project/): stg_* --> int_* --> marts (dim_legislator, fact_vote, ...)
```

Evidencia de que funciona:
- `data/legislative.duckdb` construida (8,9 MB, 2026-06-14).
- `data/raw/sitl/lxvi/sitl_votes_lxvi.csv` = **136.947** filas; `manifest.json` = **274**
  votaciones capturadas para la LXVI.
- Test singular `assert_sitl_votes_match_official_tallies` en verde: nuestra agregación
  por diputado reproduce las tallies oficiales de SITL en las 274 votaciones.

### 1.B — Camino LEGACY (roto y todavía cableado)

```
src/capture/cli.py   SCRAPERS = {"dipmex": DipMexClient, "diputados": DiputadosScraper}
flows/legislative_pipeline.py
   capture_dipmex()   -> DipMexClient.scrape()        (solo descarga padrones)
   capture_diputados()-> DiputadosScraper.scrape()    (URL equivocada; sin voto por diputado)
   load_raw_files()   -> nombres de tabla raw_{source}_{stem}  (NO coinciden con dbt)
   run_staging/analytics_transforms() -> sql/queries/*.sql  (SQL a mano, NO dbt)
   validate_data_quality() -> chequea raw_dipmex_votes_64 / raw_dipmex_deputies_64 (inexistentes)
```

Ni `SitlScraper` ni los dos `ingest_*.py` reales aparecen en el flow ni en la CLI. La capa
legacy es una isla que nunca toca el DuckDB que dbt realmente consume.

---

## 2. Diagnóstico exacto de la rotura

| # | Síntoma (premisa) | Causa raíz encontrada | Estado |
|---|---|---|---|
| D1 | "paths 404 de dipMex" | `src/capture/dipmex.py` YA corrigió los paths (`data/diputados/dip##.csv`) y `scripts/ingest_dipmex.py` baja los bundles reales `data/votesForWeb/rc{60,61}.csv.zip`. | **Arreglado** |
| D2 | "sin votos para 64-66" (dipMex) | Correcto y **estructural**: dipMex no tiene roll-calls individuales después de ~leg 62. Por eso 64/65/66 entran solo como padrón. Los **votos** de esas legislaturas vienen de SITL, no de dipMex. | **Correcto por diseño** |
| D3 | "columnas desalineadas" | `sql/ddl/01_raw_schema.sql` declara `raw_dipmex_votes`, `raw_dipmex_deputies`, `raw_diputados_votes` (DDL Snowflake) que **no coinciden** con las `sources` reales de dbt (`raw_dipmex_roster/_vote_events/_rollcall/_roster_recent`, `raw_sitl_votes/_vote_meta/_tallies`). DDL vestigial. | **Legacy muerto** |
| D4 | `DiputadosScraper` no trae voto por diputado | `VOTES_URL = https://www.diputados.gob.mx/Votaciones.htm` con `?leg=LXVI`: es el índice de resúmenes (o ni eso); NO es el endpoint SITL de 3 niveles. `SITL_BASE` hardcodeado a `LXVI_leg`. Devuelve, en el mejor caso, tallies agregadas sin `iddipt`. | **Roto / obsoleto** |
| D5 | Flow desconectado del pipeline real | `load_raw_files()` fabrica nombres `raw_{dir}_{stem}` y `validate_data_quality()` chequea `raw_dipmex_votes_64` — tablas que nunca se crean. El flow corre transforms `sql/queries/*.sql`, no `dbt build`. | **Roto / obsoleto** |
| D6 | Cobertura 64/65 | Solo existe `data/raw/sitl/lxvi/`. No hay `lxiv/` ni `lxv/`. El scraper las soporta (`LEGISLATURES = {64:"lxiv",65:"lxv",66:"lxvi"}`) pero nunca se corrió. | **Hueco real** |
| D7 | Doc dice "64-66" | README, comentarios de `sources` en `staging/schema.yml` y docstrings dicen "legs 64-66"; en disco/DB solo hay la 66. dim_legislator/fact_vote/README de hecho dicen "60, 61, 66". | **Inconsistencia doc** |

**Conclusión:** la ingestión *contra el endpoint SITL en vivo* **no está rota** — está
implementada y validada para la LXVI. Lo que está roto es (a) la orquestación legacy
paralela que nunca fue retirada, y (b) el hueco de cobertura de las legs 64 y 65.

---

## 3. (a) Patrón(es) de URL correcto(s) del SITL en vivo

Verificados dos veces: (1) contra el HTML **capturado en disco** (`data/raw/sitl/lxvi/raw/`,
3.299 páginas) y (2) el docstring de `src/capture/sitl.py`. Un `WebFetch` en vivo devolvió
**HTTP 403** — esperado: SITL bloquea User-Agents no-navegador (por eso el scraper fuerza un
UA de Chrome). Ver §7 "Qué no pude verificar".

Base: `https://sitl.diputados.gob.mx`. Slug por legislatura: 64→`lxiv`, 65→`lxv`, 66→`lxvi`.
En el path el segmento va en MAYÚSCULAS (`LXVI_leg`); en el nombre del `.php` va en minúsculas.

| Nivel | Plantilla de URL | Devuelve |
|---|---|---|
| 1. Índice de periodos | `{base}/{SEG}_leg/votaciones_por_periodonp{slug}.php` | IDs `pert=N` (periodos) |
| 2. Lista de votaciones | `{base}/{SEG}_leg/votacionesxperiodonp{slug}.php?pert=N` | IDs `votaciont=V` |
| 3. Voto por diputado | `{base}/{SEG}_leg/listados_votacionesnp{slug}.php?partidot=P&votaciont=V` | filas por diputado |
| 3b. Resumen (estadistico) | `{base}/{SEG}_leg/estadistico_votacionnp{slug}.php?votaciont=V` | fecha, título, `partidot` ids, tallies oficiales |

Ejemplo LXVI: `https://sitl.diputados.gob.mx/LXVI_leg/listados_votacionesnplxvi.php?partidot=1&votaciont=100`.

**Notas de captura (imprescindibles para T-107):**
- `partidot` es un **índice de página por-votación**, NO un id de partido estable: el mismo
  valor mapea a partidos distintos en votaciones distintas, y un partido puede abarcar varias
  páginas. El nombre del partido se lee **de la página**, no del parámetro.
- Estrategia robusta (ya en `_capture_vote`): seguir primero los `partidot` que enlaza la
  página estadistico; luego escanear `1..MAX_PARTIDOT(30)` hacia arriba, parando tras
  `EMPTY_RUN_STOP(4)` páginas vacías consecutivas (hay huecos entre páginas reales).
- Idempotencia: `manifest.json` por legislatura guarda los `votaciont` ya capturados; una
  re-corrida solo baja los nuevos y hace append. Checkpoint tras cada votación (reanudable).
- **UA de navegador obligatorio** o la respuesta es 403.

---

## 4. (b) Esquema real HTML/JSON de la respuesta

Todo es **HTML** (no hay JSON). Confirmado contra páginas guardadas.

### 4.1 Página de voto por diputado (`listados_votacionesnp...`)
Confirmado en `data/raw/sitl/lxvi/raw/v100_p1.html` (33.769 bytes):
- Tabla con **exactamente 3 celdas por fila de diputado**: `# | Diputado(a) | Sentido del voto`.
  (SITL también emite un `<tr>` envoltorio con la tabla aplanada; el guard de 3 celdas lo descarta.)
- Cada nombre es un enlace `...?iddipt=NNN`. `iddipt` = id **estable por diputado dentro de
  la legislatura**. Ejemplos reales extraídos: `iddipt=369` "Guerrero Esquivel Fuensanta
  Guadalupe", `iddipt=408` "Lara Calderón Emilio", `iddipt=407` "Rejón Lara Ariana del Rocio".
- **Formato de nombre**: `APELLIDO1 APELLIDO2 NOMBRE(S)` — apellidos primero, **sin coma**.
- Nombre del partido: se lee del string inmediatamente **anterior** al header "Diputado(a)"
  (estable entre votaciones). El título "Grupo Parlamentario LXVI" NO sirve como nombre de grupo.
- **Sentido del voto** (texto en la 3ª celda) → enum: `A favor`→FOR, `En contra`→AGAINST,
  `Abstención`→ABSTAIN, `Ausente`→ABSENT, `Solo asistencia`→PRESENT.

### 4.2 Página resumen / estadistico (`estadistico_votacionnp...`)
Confirmado en `data/raw/sitl/lxvi/raw/estadistico_v100.html` (19.762 bytes):
- **Fecha** como `DD-Mes-AAAA` en español (real: `24-Abril-2025`) → ISO. El **título** es el
  string inmediatamente anterior a la fecha.
- Enlaces `partidot=N` (reales en v100: 1,3,4,5,6,9,14) → los `partidot` exactos de esa votación.
- Tabla de **7 columnas** de tallies oficiales por partido:
  `GRUPO PARLAMENTARIO | A FAVOR | EN CONTRA | ABSTENCIÓN | SOLO ASISTENCIA | AUSENTE | TOTAL`
  (todas confirmadas presentes). Se descarta el header y la fila TOTAL general.

### 4.3 Contratos de CSV que produce el capturador (interfaz hacia dbt)
Confirmados leyendo los headers en disco:
- `sitl_votes_{slug}.csv`: `legislature, pert, votaciont, iddipt, legislator_name, party, vote_sense, vote_cast`
- `sitl_vote_meta_{slug}.csv`: `legislature, pert, votaciont, vote_date, vote_date_raw, title`
- `sitl_tallies_{slug}.csv`: `legislature, votaciont, party, a_favor, en_contra, abstencion, solo_asistencia, ausente, total`

`ingest_sitl.py` hace `UNION ALL BY NAME` de todos los `*/sitl_votes_*.csv` (etc.) y crea
`raw.raw_sitl_votes` / `_vote_meta` / `_tallies` con `CREATE OR REPLACE` (aditivo, sin red).
Esto ya soporta múltiples legislaturas automáticamente: capturar `lxiv`/`lxv` y re-correr
`ingest_sitl.py` los incorpora sin cambiar SQL.

---

## 5. (c) Mapeo de columnas: source → staging → dim → fact

### 5.1 Rama SITL (legs recientes; el foco del proyecto)

**`raw.raw_sitl_votes` → `stg_sitl_votes`** (`models/staging/stg_sitl_votes.sql`), grano
= una fila por diputado por votación:

| origen (raw_sitl_votes) | stg_sitl_votes | transform |
|---|---|---|
| `votaciont` | `vote_id` | `CAST(... AS INT)` |
| `iddipt` | `legislator_id` | `TRIM` (id estable por diputado) |
| `legislator_name` | `full_name` | `TRIM` |
| `party` | `party` | `TRIM` |
| `vote_cast` | `vote_cast` | filtra NULL/'' |
| `legislature` | `legislature` | `CAST INT` |
| — | `vote_sk` | `MD5(legislature|vote_id|legislator_id)` |
| `raw_sitl_vote_meta.vote_date` | `vote_date` | `JOIN meta USING(legislature, vote_id)` |

**`stg_sitl_votes` → `dim_legislator`** (rama SITL, `source='sitl'`): versión por **corrida
de partido fechada** (gaps-and-islands sobre `party` ordenado por `vote_date`);
`effective_from` = primera fecha de la corrida, `effective_to` = inicio de la siguiente
corrida o `end_date+1` del término. Key `MD5(source | legislator_id | legislature | effective_from)`.

**`stg_sitl_votes` → `fact_vote`**: CTE `sitl_votes` con `source='sitl'`; UNION ALL con dipMex;
LEFT JOIN a `dim_legislator` **as-of** por `(source, legislator_id)` y
`vote_date ∈ [effective_from, effective_to)`. Columnas de hecho: `vote_key`, `date_key`,
`legislator_key`, `source`, `legislator_id`, `legislature`, `vote_event_id`, `vote_cast`,
`is_affirmative`, `is_present`.

**`raw.raw_sitl_tallies`** alimenta el test `assert_sitl_votes_match_official_tallies`
(cross-check) y, vía `stg_vote_summaries`/`fact_vote_summary`, las tallies por evento.

> Nota de arquitectura: `int_votes_identified` + `int_legislator_bridge` (el puente por nombre
> difuso) están en el árbol pero **NO** los consume `fact_vote`. SITL trae `iddipt` nativo, así
> que no necesita puente; el puente queda reservado para un futuro enlace persona-entre-eras
> (ADR 004, "lo que deliberadamente NO se hace"). T-107 no debe cablearlos a `fact_vote`.

### 5.2 Rama dipMex (legs 60-61 votos; 64/65/66 solo padrón)

| modelo | source | grano |
|---|---|---|
| `stg_votes` | `raw_dipmex_rollcall` (matriz despivoteada) + `stg_vote_summaries` para fecha | voto por legislador por evento; códigos 1=FOR,2=AGAINST,3=ABSTAIN,5=ABSENT (0 y 4 excluidos) |
| `stg_vote_summaries` | `raw_dipmex_vote_events` (votdat) | un evento de votación; `vote_seq` posicional que empata la matriz |
| `stg_deputies` | `raw_dipmex_roster` (dipdat) | un legislador por legislatura; fechas de ocupación como atributos |
| `raw_dipmex_roster_recent` | `dip{64,65,66}.csv` | padrón reciente (real, sin votos) — alimenta solo la dimensión |

La matriz dipMex está keyed por el id estable → `stg_votes` lleva `legislator_id` nativo,
sin puente por nombre. dim_legislator rama dipMex: una versión por **término** de legislatura.

---

## 6. (d) Qué legislaturas están realmente disponibles

| Legislatura | Padrón | Votos por diputado | Fuente | Estado en disco/DB |
|---|---|---|---|---|
| 60 (LX) | Sí | Sí | dipMex `rc60.csv.zip` | Presente (296.200 votos) |
| 61 (LXI) | Sí | Sí | dipMex `rc61.csv.zip` | Presente (365.298 votos) |
| 62-63 | No | No | — | dipMex corta roll-calls ~62; SITL no capturado |
| 64 (LXIV) | Sí (dipMex `dip64.csv`) | **No capturado** | SITL (soportado) | **HUECO** — sin `data/raw/sitl/lxiv/` |
| 65 (LXV) | Sí (dipMex `dip65.csv`) | **No capturado** | SITL (soportado) | **HUECO** — sin `data/raw/sitl/lxv/` |
| 66 (LXVI) | Sí (dipMex `dip66.csv`) | **Sí** (274 votaciones, 136.947 filas) | SITL | Presente y validado |

**¿La 64-66 "de verdad no tiene votos" o el path está mal?** Ni lo uno ni lo otro para la 66:
la 66 SÍ tiene votos y ya están. Para 64 y 65 el **path es correcto** (mismo patrón, solo
cambia el slug); simplemente **nunca se corrió la captura**. Lo más probable es que SITL sí
exponga voto-por-diputado para 64/65 (el sistema publica legislaturas recientes), pero eso
**requiere una corrida en vivo para confirmarse** (ver §7). No hay evidencia en el repo de que
falten en la fuente; hay evidencia de que faltan en nuestra captura.

---

## 7. Qué NO pude verificar en vivo (los caveats viajan con la afirmación)

- **Fetch en vivo del SITL: bloqueado.** `WebFetch` a `votaciones_por_periodonplxvi.php`
  devolvió **HTTP 403** porque WebFetch usa un UA de bot; SITL exige UA de navegador. Esto
  *confirma* el bloqueo documentado, pero significa que **no pude reconfirmar en vivo** el
  patrón de URL ni el HTML desde esta máquina/red. La confirmación de este spec proviene del
  **HTML real capturado en disco** (autoridad: la captura verificada de Mario), que es fuente
  más fuerte que un fetch nuevo.
- **Legs 64/65 en la fuente.** No pude confirmar en vivo que SITL exponga voto-por-diputado
  para LXIV/LXV. El patrón es idéntico y es muy probable, pero la primera corrida real de
  `SitlScraper(64)` / `SitlScraper(65)` es su validación. Además la red desde la que se corra
  debe **resolver el host gubernamental** (el propio docstring del scraper lo advierte).
- **Estabilidad del `iddipt` cross-legislatura.** `iddipt` es estable *dentro* de una
  legislatura; NO asumir que el mismo humano conserva `iddipt` entre 64/65/66 (por eso la key
  conformada incluye `legislature`, y el enlace persona-entre-eras queda fuera de alcance).

---

## 8. Plan de arreglo para T-107 (accionable)

**No tocar** la lógica del camino canónico §1.A (funciona y está validado). Los cambios:

**F1 — Cerrar el hueco 64/65 (lo más valioso).**
- Correr, desde una red que resuelva `sitl.diputados.gob.mx` y con el UA de navegador ya
  incorporado: `python -m capture.sitl 64` y `python -m capture.sitl 65` (o vía `SitlScraper`).
- Re-correr `python scripts/ingest_sitl.py` (aditivo; incorpora `lxiv`/`lxv` por glob).
- `cd dbt_project && dbt build`. Verificar que `assert_sitl_votes_match_official_tallies`
  siga en verde para las nuevas votaciones (cross-check contra tallies oficiales).
- Si 64/65 resultan no tener datos por diputado en la fuente, **documentarlo como null honesto**
  (no forzar) y ajustar §6.

**F2 — Reconciliar / retirar la orquestación legacy (elige una; recomiendo B).**
- *Opción A (reconectar):* reescribir `flows/legislative_pipeline.py` para que orqueste el
  camino real (tasks: `ingest_dipmex` → `sitl_capture(64/65/66)` → `ingest_sitl` → `dbt build`),
  registrar `SitlScraper` en `src/capture/cli.py`, corregir los nombres de tabla de
  `load_raw_files`/`validate_data_quality` a las `sources` reales, y borrar el uso de
  `sql/queries/*.sql` a favor de `dbt`.
- *Opción B (retirar, recomendada):* deprecar/eliminar `DiputadosScraper` (roto, sin uso real),
  la ruta de-solo-descarga redundante de `DipMexClient`, `sql/ddl/01_raw_schema.sql`/legacy y
  la parte del flow que apunta a tablas fantasma; dejar el flow como orquestador delgado sobre
  los dos `ingest_*.py` + `dbt build`. Menos superficie, sin código muerto que engañe a un
  revisor. (Decisión de Mario; presento ambas neutralmente.)

**F3 — Alinear documentación.**
- README y comentario de `sources` en `staging/schema.yml`: decir explícitamente "SITL: LXVI
  capturada; LXIV/LXV pendientes de captura" (o "64-66" solo *después* de F1). Mantener la
  cifra de votos coherente con lo que realmente exista tras F1.

**Restricciones para T-107:** no romper el test de tallies; no cablear el bridge de nombres a
`fact_vote`; la key conformada debe seguir usando solo fechas de negocio (no churnear la FK).

---

## 9. Anclas de verificación (para el verifier / T-108)

- `src/capture/sitl.py` L108-128: builders de las 4 URLs. `src/capture/sitl.py` L52-53:
  mapa slug. L46-50: UA de navegador. L167-197: parser de página de diputado (guard 3 celdas,
  `iddipt`, nombre, sentido). L216-256: parser estadistico (fecha, título, partidots, tallies).
- `data/raw/sitl/lxvi/raw/v100_p1.html` y `estadistico_v100.html`: HTML real que confirma §4.
- `data/raw/sitl/lxvi/manifest.json`: `legislature=66`, 274 votaciones.
- `dbt_project/models/staging/stg_sitl_votes.sql`, `.../marts/dim_legislator.sql` (rama SITL
  L59-111), `.../marts/fact_vote.sql` (CTE `sitl_votes` + as-of join): confirman §5.1.
- Rotura legacy: `flows/legislative_pipeline.py` L21-22,183,229-235 (usa dipmex/diputados, no
  sitl; chequea `raw_dipmex_votes_64`); `src/capture/cli.py` L14-17; `src/capture/diputados.py`
  L53-54 (URL/base equivocados); `sql/ddl/01_raw_schema.sql` L63-102 (DDL que no coincide).
- Hueco de cobertura: `ls data/raw/sitl/` → solo `lxvi/`.
