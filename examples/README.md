# Aletheia Deep Research - Ejemplos de Uso

Esta carpeta contiene scripts de ejemplo que demuestran cómo usar la API de Aletheia Deep Research para diferentes casos de uso.

## 📋 Contenido

| Archivo | Lenguaje | Descripción | Tiempo estimado |
|---------|----------|-------------|-----------------|
| `simple_research.sh` | Bash | Investigación simple con monitoreo automático | 30-60s |
| `simple_research.py` | Python | Investigación simple con cliente Python | 30-60s |
| `deep_research.py` | Python | Investigación profunda iterativa con métricas | 2-5 min |

## 🚀 Pre-requisitos

Antes de ejecutar los ejemplos, asegúrate de:

1. **Tener la API corriendo:**
```bash
uvicorn apps.api.main:app --reload
```

2. **Verificar que la API esté funcionando:**
```bash
curl http://localhost:8000/health
```

3. **Tener las dependencias instaladas (para Python):**
```bash
pip install requests
```

4. **Configurar las API keys en `.env`:**
```bash
SAPTIVA_API_KEY=tu_key_aqui
TAVILY_API_KEY=tu_key_aqui
```

## 📖 Ejemplos de Uso

### 1. Simple Research (Bash)

Script bash completo con manejo de errores y formateo de salida.

**Uso básico:**
```bash
# Con query por defecto
bash examples/simple_research.sh

# Con query personalizada
bash examples/simple_research.sh "Análisis del mercado de fintech en México"
```

**Características:**
- ✅ Verificación automática de API health
- ✅ Monitoreo de progreso con timeout
- ✅ Guardado automático del reporte
- ✅ Preview del reporte en terminal
- ✅ Manejo de errores detallado

**Salida:**
```bash
========================================
Aletheia Deep Research - Simple Example
========================================

1. Verificando que la API esté corriendo...
✅ API corriendo correctamente

2. Iniciando investigación...
   Query: Últimas tendencias en inteligencia artificial 2025
✅ Investigación iniciada
   Task ID: 550e8400-e29b-41d4-a716-446655440000

3. Monitoreando progreso...
   Status: running (intento 1/60)
   Status: running (intento 2/60)
   ...
✅ Investigación completada!

4. Obteniendo reporte...

========================================
📊 RESUMEN
========================================
Task ID:    550e8400-e29b-41d4-a716-446655440000
Status:     ✅ Completado
Fuentes:    Generated from 15 evidence sources
Reporte:    report_20251022_153045.md

🎉 Investigación completada exitosamente!
```

### 2. Simple Research (Python)

Cliente Python completo con manejo de excepciones.

**Uso básico:**
```bash
# Con query por defecto
python3 examples/simple_research.py

# Con query personalizada
python3 examples/simple_research.py "Impacto de blockchain en supply chain"

# Configurar URL de API custom
API_URL=http://production-api.com python3 examples/simple_research.py "Query"
```

**Características:**
- ✅ Cliente Python orientado a objetos
- ✅ Type hints para mejor IDE support
- ✅ Manejo robusto de excepciones
- ✅ Timeout configurable
- ✅ Guardado automático con timestamp

**Uso programático:**
```python
from examples.simple_research import check_api_health, start_research, get_report

# Verificar API
if check_api_health("http://localhost:8000"):
    # Iniciar investigación
    task_id = start_research("http://localhost:8000", "Tu query")

    # Esperar y obtener reporte
    # ... (ver código completo)
```

### 3. Deep Research (Python)

Cliente avanzado para investigaciones profundas con métricas de calidad.

**Uso básico:**
```bash
# Con parámetros por defecto
python3 examples/deep_research.py

# Con query personalizada
python3 examples/deep_research.py "Estado del arte en Large Language Models"

# Con parámetros avanzados
python3 examples/deep_research.py \
  --iterations 5 \
  --min-score 0.90 \
  --budget 300 \
  "Análisis comparativo de frameworks de machine learning"
```

**Parámetros disponibles:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `query` | string | - | Consulta de investigación (posicional) |
| `--iterations` | int | 3 | Número máximo de iteraciones (1-10) |
| `--min-score` | float | 0.85 | Score mínimo de completitud (0.1-1.0) |
| `--budget` | int | 200 | Presupuesto total para la investigación |
| `--api-url` | string | http://localhost:8000 | URL de la API |

**Características:**
- ✅ Investigación iterativa con refinamiento
- ✅ Evaluación automática de completitud
- ✅ Gap analysis
- ✅ Métricas de calidad detalladas
- ✅ Resumen estructurado de hallazgos
- ✅ Argumentos de línea de comandos

**Salida:**
```bash
========================================
🔬 Aletheia Deep Research - Deep Research Example
========================================

1️⃣  Verificando API...
✅ API disponible

2️⃣  Iniciando Deep Research...
   Query:              Impacto de la inteligencia artificial...
   Max Iterations:     5
   Min Completion:     90%
   Budget:             300

✅ Deep Research iniciado
   Task ID: deep-550e8400-e29b-41d4-a716-446655440000

3️⃣  Monitoreando progreso...
   [0.5s] Status: running (intento 1/120)
   [5.5s] Status: running (intento 2/120)
   ...
   [127.3s] Status: completed

✅ Deep Research completado!

4️⃣  Resultados:
========================================

📊 Métricas de Calidad:
   • Completion Level:  95%
   • Quality Score:     88%
   • Evidence Count:    42
   • Execution Time:    127.3s

📋 Resumen de Investigación:
   • Iteraciones:       3
   • Brechas:           regulatory_compliance, market_impact
   • Hallazgos clave:
     - High compliance costs
     - Market consolidation likely

💾 Reporte guardado en: deep_research_impacto_ia_20251022_153045.md

🎉 Deep Research completado exitosamente!
```

## 🎯 Casos de Uso Recomendados

### Análisis de Mercado
```bash
python3 examples/simple_research.py \
  "Análisis del mercado de vehículos eléctricos en América Latina 2025"
```

### Due Diligence Técnico
```bash
python3 examples/deep_research.py \
  --iterations 5 \
  --min-score 0.90 \
  "Evaluación técnica de arquitecturas de microservicios: Kubernetes vs Serverless"
```

### Investigación Académica
```bash
python3 examples/deep_research.py \
  --iterations 7 \
  --budget 400 \
  "Estado del arte en quantum machine learning: algoritmos y aplicaciones"
```

### Monitoreo de Tendencias
```bash
python3 examples/simple_research.py \
  "Últimas tendencias en ciberseguridad: amenazas emergentes 2025"
```

## 🛠 Personalización

### Crear tu propio script

```python
#!/usr/bin/env python3
import requests

API_URL = "http://localhost:8000"

# 1. Iniciar investigación
response = requests.post(
    f"{API_URL}/research",
    json={"query": "Tu consulta"}
)
task_id = response.json()["task_id"]

# 2. Esperar completitud (simplificado)
import time
while True:
    status = requests.get(f"{API_URL}/tasks/{task_id}/status")
    if status.json()["status"] == "completed":
        break
    time.sleep(5)

# 3. Obtener reporte
report = requests.get(f"{API_URL}/reports/{task_id}")
print(report.json()["report_md"])
```

### Integración en aplicaciones

Para integrar en tus aplicaciones Python, puedes:

1. **Importar funciones de los ejemplos:**
```python
from examples.simple_research import start_research, monitor_task, get_report
```

2. **Usar requests directamente:**
```python
import requests

def research(query: str) -> dict:
    response = requests.post(
        "http://localhost:8000/research",
        json={"query": query}
    )
    return response.json()
```

3. **Crear un cliente dedicado:**
```python
from examples.deep_research import DeepResearchClient

client = DeepResearchClient()
task_id = client.start_deep_research("Query", max_iterations=5)
result = client.monitor_research(task_id)
```

## 🐛 Troubleshooting

### Error: "Connection refused"
La API no está corriendo. Inicia con:
```bash
uvicorn apps.api.main:app --reload
```

### Error: "API key not configured"
Configura tus API keys en `.env`:
```bash
cp .env.example .env
# Edita .env con tus keys
```

### Error: "Permission denied"
Dale permisos de ejecución al script bash:
```bash
chmod +x examples/simple_research.sh
```

### Timeout en investigaciones
Aumenta el timeout en los scripts o ajusta parámetros:
```python
# En simple_research.py
MAX_ATTEMPTS = 120  # 10 minutos
```

## 📚 Recursos Adicionales

- **Documentación completa:** [README.md](../README.md)
- **API Reference:** http://localhost:8000/docs (cuando el servidor esté corriendo)
- **Test Suite:** `python3 tools/testing/test_apis.py`
- **GitHub Issues:** https://github.com/saptiva-ai/alethia_deepresearch/issues

## 💡 Tips

1. **Experimenta con parámetros:** Ajusta `max_iterations` y `min_completion_score` según tu caso de uso
2. **Guarda los reportes:** Los scripts ya guardan automáticamente, pero puedes personalizar el formato
3. **Monitorea recursos:** Deep research puede consumir más recursos, ajusta el `budget` según necesidad
4. **Usa queries específicas:** Queries más específicas generan mejores resultados
5. **Combina enfoques:** Usa simple research para exploración rápida, deep research para análisis profundo

## 🤝 Contribuir

¿Tienes un caso de uso interesante? ¡Contribuye con tu ejemplo!

1. Crea tu script en esta carpeta
2. Documéntalo en este README
3. Envía un Pull Request

---

**¿Preguntas?** Abre un issue en GitHub o consulta la documentación completa.
