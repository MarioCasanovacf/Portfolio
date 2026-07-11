# Fuentes del Benchmark de Frontera (Julio 2026)

Este documento recopila las métricas de calidad, precio y rendimiento de los modelos de frontera de punta actuales. Estos datos se utilizan para la comparación cualitativa y cuantitativa en el benchmark del caso de estudio contra el modelo local.

**Fecha de consulta:** 8 de julio de 2026  
**Fuentes de referencia principales:** 
- [Artificial Analysis](https://artificialanalysis.ai) (accedido el 08-07-2026)
- [LMSYS Chatbot Arena Leaderboard](https://lmarena.ai) (accedido el 08-07-2026)
- Páginas de precios oficiales de los proveedores (OpenAI, Anthropic, Google Cloud Vertex AI y DeepSeek API).

---

## 1. Calidad General y Preferencia Humana (LMSYS Chatbot Arena)

Clasificación de los modelos de frontera líderes basada en pruebas ciegas de preferencia humana (Elo general).

| Modelo | Desarrollador | Rango Elo Típico (Arena) | Notas y Fortalezas |
| :--- | :--- | :--- | :--- |
| **Claude Opus 4.8** | Anthropic | ~1320–1330 | Líder indiscutible en razonamiento complejo, tareas de programación (SWE-bench Pro) y flujos de trabajo basados en agentes. |
| **GPT-5.5** | OpenAI | ~1315–1325 | Excelente desempeño en ejecución interactiva en terminales, orquestación de herramientas externas y persistencia de instrucciones. |
| **Gemini 3.1 Pro** | Google | ~1290–1300 | Alta velocidad de respuesta y óptima retención de contexto largo (2M+ tokens), ideal para flujos multimodales empresariales. |
| **GLM-5.2** | Zhipu AI | ~1260–1270 | Modelo open-weights de alta capacidad y desempeño equilibrado en múltiples lenguajes. |
| **DeepSeek V4 Pro** | DeepSeek | ~1250–1260 | Modelo de alta gama muy competitivo en tareas lógicas y de código a una fracción del costo de la competencia occidental. |

---

## 2. Precios de API oficiales (Costo por 1 Millón de Tokens)

Costos vigentes bajo las APIs directas de los desarrolladores (precios de lista oficiales).

| Modelo / API | Costo de Entrada (Input por 1M) | Costo de Salida (Output por 1M) | Proveedor / Endpoint Canónico |
| :--- | :--- | :--- | :--- |
| **GPT-5.5** | $5.00 | $30.00 | OpenAI API |
| **Claude Opus 4.8** | $5.00 | $25.00 | Anthropic API |
| **Gemini 3.1 Pro** | $2.00 | $12.00 | Google Vertex AI / AI Studio |
| **GLM-5.2** | $1.40 | $4.40 | Zhipu / Open-Weights hosters |
| **DeepSeek V4 Flash** | $0.14 | $0.28 | DeepSeek API (El API de frontera más barato del mercado) |

---

## 3. Latencia y Rendimiento Técnico (Artificial Analysis)

El comportamiento de latencia en la inferencia en tiempo real varía considerablemente por la escala del modelo.

- **Líderes en Latencia (Time-to-First-Token - TTFT):**
  - **Gemini 2.5 Flash:** Registra un TTFT promedio inferior a **600ms** en prompts de longitud mediana.
  - **Claude Haiku 4.5:** Registra un TTFT promedio inferior a **600ms** en prompts de longitud mediana.
  Ambos son los modelos preferidos para interacciones conversacionales rápidas y flujos secuenciales donde la respuesta inicial bloquea al usuario.
  
- **Modelos de Gran Escala (Opus/GPT-5.5):**
  - **Claude Opus 4.8:** TTFT de **1200ms–1800ms** debido a su gran tamaño de parámetros y los pasos de enrutamiento interno.
  - **GPT-5.5:** TTFT de **1100ms–1600ms** bajo condiciones normales de carga.

---

## 4. Comparación Cualitativa Estructural

- **Privacidad:** La transmisión de datos del cliente por internet es obligatoria con APIs externas. El modelo local ofrece una garantía de residencia de datos absoluta en la máquina local.
- **Determinismo:** El comportamiento de modelos remotos de gran escala a menudo sufre de fluctuaciones silenciosas causadas por cambios de enrutamiento o actualizaciones de infraestructura del proveedor. El modelo local ejecutado en hardware local (`distilbert-base-multilingual-cased` con semilla fija) ofrece un determinismo perfecto y repetible.
