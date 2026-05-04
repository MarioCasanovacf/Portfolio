# ADR 001: Orchestrator Choice — Prefect over Airflow

**Status:** Accepted
**Date:** 2026-03-24
**Context:** Necesitamos un orquestador para el pipeline de datos legislativos.

## Opciones Evaluadas

### Apache Airflow
- **Pro:** Estándar de industria. Enorme ecosistema de operadores y providers.
- **Pro:** Scheduler daemon permanente — ideal para pipelines críticos 24/7.
- **Contra:** Overhead operacional significativo: base de datos (PostgreSQL), webserver, scheduler, workers. Excesivo para un portafolio personal.
- **Contra:** DSL basado en DAGs declarativos. La lógica compleja requiere workarounds.
- **Contra:** Testing de DAGs es notoriamente difícil.

### Prefect
- **Pro:** API puramente Pythonic — flows y tasks son funciones Python decoradas.
- **Pro:** Cero infraestructura para desarrollo local: `python flow.py` ejecuta el pipeline.
- **Pro:** Retries, caching, y logging integrados sin configuración adicional.
- **Pro:** Prefect Cloud ofrece free tier para monitoreo (opcional).
- **Contra:** Menos adoption que Airflow en empresas Fortune 500.

### Dagster
- **Pro:** Paradigma de software-defined assets es elegante para modelado de dependencias.
- **Pro:** Excelente UI de desarrollo (Dagit).
- **Contra:** Curva de aprendizaje más pronunciada. Conceptos como IOManagers y Resources añaden complejidad inicial.
- **Contra:** Menor comunidad que Prefect para troubleshooting.

## Decisión

**Prefect** como orquestador principal.

## Justificación

Para un proyecto de portafolio que debe ser:
1. **Ejecutable localmente** sin Docker ni bases de datos auxiliares
2. **Legible** por reviewers que no conocen el framework
3. **Testeable** con pytest estándar

Prefect ofrece la mejor relación señal/ruido. El pipeline completo se ejecuta con `python flows/legislative_pipeline.py`. No hay daemon que mantener, no hay UI que desplegar, no hay metadata database que migrar.

En un entorno empresarial con múltiples pipelines y SLAs, Airflow sería la decisión correcta. Para demostrar competencia en orquestación con mínimo overhead, Prefect gana.

## Consecuencias

- Los flows son funciones Python puras: portables a cualquier orquestador futuro.
- Si se migra a producción con Airflow, el refactor es mecánico (decorators → DAG operators).
- Se pierde el scheduling basado en cron nativo (Airflow); se compensa con Prefect schedules o cron del sistema.
