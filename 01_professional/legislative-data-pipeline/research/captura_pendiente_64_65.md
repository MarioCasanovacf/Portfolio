# Captura pendiente: legislaturas 64 (LXIV) y 65 (LXV) del SITL

**Para:** Mario. **Contexto:** T-107, siguiendo el spec de T-106
(`research/ingestion_fix_spec.md`, §6 y §8-F1). **Fecha:** 2026-07-05.

## Por qué esto lo tienes que correr tú

El scraper (`src/capture/sitl.py`, clase `SitlScraper`) ya soporta las tres
legislaturas recientes (`LEGISLATURES = {64: "lxiv", 65: "lxv", 66: "lxvi"}`)
con el mismo patrón de URL verificado para la 66. El único motivo por el que
64 y 65 no están capturadas es que **nunca se corrió** — no un bug. Pero el
host `sitl.diputados.gob.mx` no resuelve desde esta red de trabajo (agente),
y SITL exige un User-Agent de navegador real (ya está forzado en el
scraper) más una IP que no esté bloqueada. Por eso este agente NO intentó
correr la captura en vivo — necesita tu Mac, con tu red.

## Comando exacto

Desde la raíz del proyecto (`legislative-data-pipeline/`), con el venv de
captura (`.venv`, el mismo que ya tiene `httpx`, `beautifulsoup4`, `structlog`
instalados vía `pip install -e ".[dev]"`):

```bash
cd Portfolio-repo/01_professional/legislative-data-pipeline

# Legislatura 64 (LXIV)
.venv/bin/python -m capture.sitl 64

# Legislatura 65 (LXV)
.venv/bin/python -m capture.sitl 65
```

Cada corrida:
- Es **incremental y reanudable**: `data/raw/sitl/{lxiv,lxv}/manifest.json`
  guarda los `votaciont` ya capturados; si se interrumpe (Ctrl-C, corte de
  red), volver a correr el mismo comando retoma donde quedó — no duplica.
- Escribe `data/raw/sitl/{lxiv,lxv}/sitl_votes_{slug}.csv`,
  `sitl_vote_meta_{slug}.csv`, `sitl_tallies_{slug}.csv` — mismo contrato de
  columnas que ya usa la LXVI (ver `research/ingestion_fix_spec.md` §4.3).
- Puede tardar (recorre periodo → lista de votaciones → voto-por-diputado
  para cada `votaciont`); la LXVI capturada tiene 274 votaciones. Correrlo en
  segundo plano o con `nohup` si son muchas.

## Cómo se integra después (sin tocar nada más)

Una vez que existan `data/raw/sitl/lxiv/` y/o `data/raw/sitl/lxv/` con esos
tres CSV + manifest, la integración es **aditiva y automática** — no hay que
cambiar código:

```bash
python scripts/ingest_sitl.py      # sin red; hace glob de */sitl_votes_*.csv
                                    # y recrea raw.raw_sitl_votes/_vote_meta/_tallies
                                    # con UNION ALL BY NAME sobre TODAS las slugs presentes
cd dbt_project && dbt build        # staging + marts + tests, incluida
                                    # assert_sitl_votes_match_official_tallies
                                    # para las votaciones nuevas
```

Este agente ya verificó que `ingest_sitl.py` hace `UNION ALL BY NAME` por
glob (`SITL_DIR.glob("*/sitl_votes_*.csv")`), así que agregar `lxiv/` o
`lxv/` no requiere ningún cambio en `scripts/ingest_sitl.py` ni en los
modelos dbt (`stg_sitl_votes.sql` ya lee de `raw.raw_sitl_votes` sin filtrar
por legislatura).

## Qué NO está garantizado (caveats que viajan con la afirmación)

- No hay confirmación en vivo de que SITL exponga voto-por-diputado para
  64/65 (es muy probable — el patrón de URL es idéntico y el sistema publica
  legislaturas recientes — pero la primera corrida real es la que lo
  confirma). Si alguna de las dos legislaturas resulta sin datos por
  diputado en la fuente, lo correcto es documentarlo como **hueco honesto**
  en el README (no forzar un valor).
- El `iddipt` es estable **dentro** de cada legislatura, no entre
  legislaturas — no asumas que el mismo diputado conserva el mismo `iddipt`
  en 64 vs. 65 vs. 66 (el puente persona-entre-eras queda fuera de alcance,
  ver ADR 004).
- Tras capturar, conviene actualizar el README (tabla "Data sources" y el
  comentario de `sitl.py` en el árbol de proyecto) para que diga "64/65/66"
  en vez de "66 capturada; 64/65 pendientes" — este agente ya deja esa
  redacción provisional en `README.md` apuntando aquí.
