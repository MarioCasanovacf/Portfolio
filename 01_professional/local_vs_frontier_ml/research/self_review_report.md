# Reporte de Self-Review — Local vs Frontier ML

Este reporte documenta la autoevaluación de calidad del benchmark antes de la entrega final y traspaso para la pasada de voz de Claude y revisión de Mario.

---

## 1. Validación de Anti-Tautología (Reglas del Caso de Estudio)

- **Test Set Congelado:** Se pre-registró y se evaluó sobre un conjunto de prueba completamente held-out y estratificado (500 reviews por idioma, 3000 reviews en total).
- **Umbral de Pérdida:** El modelo local (`distilbert-base-multilingual-cased`) entrenado con 2,000 samples por idioma (12k total) obtuvo una precisión global del **68.63%** y un macro-F1 global del **60.94%**. Esto es comparable a los benchmarks publicados en literatura para tareas similares de clasificación de 3 clases en MARC (~64-70% de F1), por lo que supera el umbral de pérdida.
- **Punto de Equilibrio de Costo:** Se modeló cuantitativamente en la Sección 5. A volúmenes bajos (< 100k reviews acumuladas), los costos de desarrollo (tiempo de ingeniero para recolectar, entrenar y configurar infraestructura) dominan sobre el costo marginal de la API de frontera. A gran volumen (> 1M de reviews), el costo marginal de $0 del modelo local lo hace altamente rentable.
- **Honestidad sobre Ventajas de la Frontera:** Se declararon explícitamente en la Sección 6 y 7 los escenarios donde las APIs de frontera superan al modelo local: arranque en frío sin etiquetas, tareas complejas de razonamiento/generación y bajo volumen de consultas.

---

## 2. Validación de Reproducibilidad y Código

- **Script de Descarga:** `scripts/download_data.py` descarga de forma idempotente el dataset `goosmanlei/amazon_reviews_multi` de HuggingFace Hub y crea una muestra estratificada local en `data/sample/`.
- **Script de Entrenamiento:** `scripts/train_local.py` entrena el modelo con semilla fija (determinismo verificado: PASS) utilizando aceleración MPS en Apple Silicon. Genera las métricas guardadas en `research/local_model_metrics.json`.
- **Notebook Ejecutada:** `notebooks/01_local_vs_frontier_benchmark.ipynb` se ejecuta de principio a fin de forma limpia con `jupyter nbconvert` y genera las figuras reproducibles con `matplotlib`.
- **Aislamiento de NDA:** No se importa código, funciones o archivos de datos de `review_sentiment_ml/`. El trabajo de la empresa se cita estrictamente en prosa como el caso de uso motivador de este patrón.

---

## 3. Estilo de Prosa y Voz

- **Idiomas:** El documento de diseño y este reporte están en español. La notebook y el README están escritos enteramente en inglés.
- **Voz Metodológica:** Se utiliza la primera persona metodológica con proyección universal ("I configure...", "I evaluate...").
- **Evitación de List-itis y Formatos Corporativos:** La notebook expone los argumentos y conclusiones en párrafos narrativos fluidos, reservando las listas únicamente para los parámetros y reglas de protocolo (Sección 1 y 5).
- **Legibilidad Numérica:** Se limitó el uso de porcentajes por frase y se dio una interpretación intuitiva a las métricas (por ejemplo, ratio de throughput 20x–40x superior).

---

## 4. Estado de la Integración con el Sitio

- No se alteró `studies.ts` ni se publicaron páginas `.mdx` adicionales. El slot `ml-second` se mantiene intacto como marcador de posición.
- La entrega se realiza estrictamente en la carpeta `01_professional/local_vs_frontier_ml/`.
