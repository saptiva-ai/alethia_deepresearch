# 📚 Documentación API - Aletheia Deep Research v0.7.0

## 🔍 Descripción General

La API de Aletheia Deep Research proporciona capacidades avanzadas de investigación automatizada con dos modos principales:

- **Investigación Estándar**: Procesamiento paralelo optimizado para consultas directas
- **Investigación Profunda**: Refinamiento iterativo usando patrón Together AI

## 🚀 Características Principales

### ✨ **Optimización de Alto Rendimiento**
- Procesamiento paralelo de sub-tareas de investigación
- Cache inteligente para endpoints de salud (TTL: 30s)
- Validación de API keys con cache LRU
- Arquitectura asíncrona completa

### 🔄 **Investigación Iterativa (Deep Research)**
- Evaluación automática de completitud con scores 0.0-1.0
- Identificación de gaps de información
- Refinamiento automático hasta alcanzar objetivos de calidad
- Control granular de presupuesto y iteraciones

### 📊 **Observabilidad Completa**
- Trazabilidad OpenTelemetry integrada
- Logging estructurado de eventos
- Métricas de rendimiento en tiempo real
- Exportación de artefactos de auditoría

## 📋 Endpoints Disponibles

### 🏥 Estado del Sistema
- **GET** `/health` - Verificación de estado con API keys

### 🔍 Investigación Estándar  
- **POST** `/research` - Iniciar investigación con procesamiento paralelo
- **GET** `/tasks/{task_id}/status` - Consultar estado de tarea
- **GET** `/reports/{task_id}` - Obtener reporte completo

### 🧠 Investigación Profunda
- **POST** `/deep-research` - Iniciar investigación iterativa
- **GET** `/deep-research/{task_id}` - Obtener resultado con métricas de calidad

### 📈 Observabilidad
- **GET** `/traces/{task_id}` - Obtener trazas OpenTelemetry

## 🔧 Configuración

### Variables de Entorno Requeridas
```bash
SAPTIVA_API_KEY=tu_clave_saptiva_aqui
TAVILY_API_KEY=tu_clave_tavily_aqui

# Opcional - OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=alethia-deep-research

# Opcional - Almacenamiento de artefactos
ARTIFACTS_DIR=./runs
```

### Dependencias
```bash
pip install -r requirements.txt
```

## 🚀 Inicio Rápido

### 1. Levantar la API
```bash
# Modo desarrollo
uvicorn apps.api.main:app --reload --port 8000

# Modo producción
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Verificar Estado
```bash
curl http://localhost:8000/health
```

### 3. Investigación Estándar
```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Análisis del mercado de inteligencia artificial en 2025",
    "budget": 50.0
  }'
```

### 4. Investigación Profunda
```bash
curl -X POST "http://localhost:8000/deep-research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Impacto de la regulación AI Act en startups europeas",
    "max_iterations": 5,
    "min_completion_score": 0.85,
    "budget": 200
  }'
```

## 📊 Modelos de Datos

### ResearchRequest
```json
{
  "query": "string (requerido)",
  "scope": "string (opcional)",
  "budget": "number (0-1000, opcional)"
}
```

### DeepResearchRequest  
```json
{
  "query": "string (requerido)",
  "scope": "string (opcional)",
  "max_iterations": "integer (1-10, default: 3)",
  "min_completion_score": "number (0.1-1.0, default: 0.75)",
  "budget": "integer (1-5000, default: 100)"
}
```

### TaskStatus
```json
{
  "task_id": "uuid",
  "status": "accepted|running|completed|failed",
  "details": "string (opcional)"
}
```

### DeepResearchReport
```json
{
  "status": "completed|failed|running",
  "report_md": "string - Reporte en Markdown",
  "sources_bib": "string - Bibliografía",
  "research_summary": {
    "iterations_completed": "integer",
    "gaps_identified": ["array de strings"],
    "key_findings": ["array de strings"]
  },
  "quality_metrics": {
    "completion_level": "number (0-1)",
    "quality_score": "number (0-1)", 
    "evidence_count": "integer",
    "execution_time": "number (segundos)"
  }
}
```

## 🏗️ Arquitectura

### Stack Tecnológico
- **Framework**: FastAPI 0.100+
- **Async Runtime**: asyncio/uvicorn
- **Validación**: Pydantic v2
- **Observabilidad**: OpenTelemetry
- **AI Models**: Saptiva Cortex API
- **Search**: Tavily API
- **Vector Storage**: Weaviate (opcional)

### Patrones de Diseño
- **Puertos y Adaptadores**: Arquitectura hexagonal
- **Repository Pattern**: Abstracción de almacenamiento
- **Observer Pattern**: Eventos de telemetría
- **Strategy Pattern**: Múltiples proveedores de AI/Search

## 🔒 Seguridad

### Rate Limiting
- Implementado en `adapters/security/rate_limiter.py`
- Límites configurables por endpoint y usuario
- Protección contra DDoS y abuso

### Validación de Entrada
- Sanitización automática de queries con `BasicGuardAdapter`
- Validación de parámetros con Pydantic
- Límites de presupuesto y recursos

### Auditoría
- Logging completo de todas las operaciones
- Trazas distribuidas para debugging
- Exportación de artefactos para compliance

## 📈 Métricas y Monitoreo

### Métricas Clave
- **Latencia**: Tiempo de respuesta por endpoint
- **Throughput**: Requests por segundo  
- **Success Rate**: % de investigaciones exitosas
- **Quality Score**: Puntuación promedio de investigaciones
- **Resource Usage**: Consumo de API keys y presupuesto

### Dashboards
- Grafana con métricas de OpenTelemetry
- Jaeger para trazas distribuidas
- Alertas en Prometheus

## 🧪 Testing

### Pruebas de Rendimiento
```bash
# Load test rápido
python tools/benchmarks/quick_load_test.py

# Suite completa de benchmarks  
python tools/benchmarks/benchmark_performance.py
```

### Métricas de Referencia
- **Health Check**: >100 req/s, <100ms
- **Research Endpoint**: <1000ms latency inicial
- **Deep Research**: 3-5 iteraciones promedio
- **Success Rate**: >95% en condiciones normales

## 📚 Documentación Adicional

### Especificaciones OpenAPI
- **JSON**: [`openapi.json`](./openapi.json)  
- **YAML**: [`openapi.yaml`](./openapi.yaml)
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Arquitectura del Sistema
- [Guía de CI/CD](../guides/CI_CD_GUIDE.md)
- [Roadmap de Testing](../roadmaps/TESTING_ROADMAP.md)
- [Reportes de Rendimiento](../roadmaps/performance_report.md)

## 🤝 Contribución

### Flujo de Desarrollo
1. Fork del repositorio
2. Crear feature branch
3. Implementar cambios con tests
4. Ejecutar suite de pruebas completa
5. Pull Request con documentación actualizada

### Estándares de Código
- Type hints completos (Python 3.8+)
- Documentación docstrings
- Tests unitarios >95% cobertura
- Validación con linters (ruff, mypy)

---

**📍 Versión**: v0.7.0 ENTERPRISE-READY CI/CD COMPLETE  
**📅 Última Actualización**: 12 de Septiembre, 2025  
**👥 Mantenido por**: Aletheia Development Team  
**🔗 Repositorio**: [GitHub](https://github.com/saptiva-ai/alethia_deepresearch)