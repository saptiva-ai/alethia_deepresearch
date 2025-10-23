# 🧪 Guía de Pruebas - Aletheia Deep Research

Esta guía te muestra cómo probar todas las funcionalidades del sistema, incluyendo:
- ✅ Research (investigación simple)
- ✅ Deep Research (investigación profunda con WebSocket)
- ✅ Guardado de reportes en MongoDB
- ✅ Trazabilidad completa

---

## 🚀 Prueba Rápida (2 minutos)

### Script Automático

El script de prueba rápida verifica los componentes básicos:

```bash
./tools/quick_test.sh
```

**Verifica:**
- Health check de la API
- Endpoint `/research` funcionando
- Generación de reportes básica

---

## 🔍 Verificación Completa (5 minutos)

### Script de Verificación Completo

Este es el script **más completo** que verifica TODAS las funcionalidades:

```bash
python tools/verify_system.py
```

**Este script verifica:**

### 1️⃣ Variables de Entorno
- ✅ SAPTIVA_API_KEY configurada
- ✅ TAVILY_API_KEY configurada
- ✅ MONGODB_URL configurada (opcional)

### 2️⃣ API Health
- ✅ API corriendo en puerto 8000
- ✅ Health endpoint respondiendo
- ✅ API keys disponibles en el servidor

### 3️⃣ Research Simple (`/research`)
- ✅ Iniciar investigación
- ✅ Monitorear status
- ✅ Obtener reporte completo
- ✅ Verificar fuentes documentadas

### 4️⃣ Deep Research con WebSocket (`/deep-research`)
- ✅ Iniciar investigación profunda
- ✅ Conectar WebSocket para actualizaciones en tiempo real
- ✅ Recibir eventos: started, planning, iteration, evidence, evaluation, completed
- ✅ Obtener reporte final con métricas de calidad
- ✅ Verificar resumen de investigación

### 5️⃣ MongoDB (si está configurado)
- ✅ Conexión a base de datos
- ✅ Collections: tasks, reports, logs
- ✅ Verificar que los reportes se guardaron correctamente
- ✅ Estadísticas de documentos almacenados

**Salida Esperada:**
```
======================================================================
  📋 RESUMEN FINAL
======================================================================

   Tests ejecutados: 20
   ✅ Pasados: 20
   ❌ Fallados: 0
   ⚠️  Advertencias: 0

   Tasa de éxito: 100.0%

   🎉 ¡TODOS LOS TESTS PASARON! El sistema está funcionando correctamente.
```

---

## 🧪 Pruebas Manuales Paso a Paso

### Prueba 1: Research Simple

```bash
# 1. Iniciar investigación
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Últimas tendencias en IA 2025"}'

# Respuesta esperada:
# {
#   "task_id": "abc-123-def-456",
#   "status": "accepted",
#   "details": "Research task has been accepted..."
# }

# 2. Copiar el task_id y consultar status (espera ~30 segundos)
TASK_ID="abc-123-def-456"  # Reemplaza con tu task_id
curl "http://localhost:8000/tasks/$TASK_ID/status"

# 3. Obtener reporte cuando status = "completed"
curl "http://localhost:8000/reports/$TASK_ID" | jq -r '.report_md'
```

**¿Qué verificar?**
- ✅ El task_id se genera correctamente
- ✅ El status cambia de "accepted" → "running" → "completed"
- ✅ El reporte se genera en formato Markdown
- ✅ Las fuentes están documentadas

---

### Prueba 2: Deep Research con WebSocket

Usa el script de ejemplo incluido:

```bash
python examples/deep_research.py "Impacto de la IA en el mercado laboral"
```

**Salida esperada (actualizaciones en tiempo real):**
```
🔬 Aletheia Deep Research - Deep Research Example
======================================================================

1️⃣  Verificando API...
✅ API disponible

2️⃣  Iniciando Deep Research...
   Query:              Impacto de la IA en el mercado laboral
   Max Iterations:     3
   Min Completion:     85%
   Budget:             200

✅ Deep Research iniciado
   Task ID: abc-123-def-456

3️⃣  Monitoreando progreso en tiempo real (esto puede tomar varios minutos)...
   📡 Usando WebSocket para actualizaciones instantáneas... (Ctrl+C para cancelar)

   📡 Conectando a WebSocket: ws://localhost:8000/ws/progress/abc-123-def-456
   ✅ WebSocket conectado - recibiendo actualizaciones en tiempo real

   🚀 [0.1s] Starting deep research: Impacto de la IA en el mercado laboral
   📋 [2.3s] Research plan created with 5 sub-tasks
   🔄 [2.5s] Starting iteration 1/3
   🔍 [15.2s] Collected 12 new evidence items (total: 12)
   📊 [16.1s] Completion score: 45% (PRELIMINARY)
      └─ Score: 0.45
   🎯 [17.8s] Identified 3 information gaps
      └─ Top gaps: market_data, regulatory_info
   🔧 [18.2s] Generated 4 refinement queries for next iteration
   🔄 [18.5s] Starting iteration 2/3
   🔍 [32.1s] Collected 8 new evidence items (total: 20)
   📊 [33.0s] Completion score: 78% (COMPREHENSIVE)
      └─ Score: 0.78
   🎯 [34.2s] Identified 2 information gaps
   🔧 [34.5s] Generated 2 refinement queries for next iteration
   🔄 [34.8s] Starting iteration 3/3
   🔍 [45.3s] Collected 5 new evidence items (total: 25)
   📊 [46.1s] Completion score: 92% (COMPREHENSIVE)
      └─ Score: 0.92
   📝 [46.5s] Generating final report...
   ✅ [52.3s] Deep research completed! 25 evidence items, quality score: 92%

✅ Investigación completada en 52.3s

4️⃣  Resultados:
======================================================================

📊 Métricas de Calidad:
   • Completion Level:  92%
   • Quality Score:     88%
   • Evidence Count:    25
   • Execution Time:    52.3s

📋 Resumen de Investigación:
   • Iteraciones:       3
   • Brechas:           market_data, regulatory_info
   • Hallazgos clave:
     - IA está transformando roles tradicionales
     - Necesidad de reskilling masivo

💾 Reporte guardado en: deep_research_Impacto_de_la_IA_20251022_153045.md

🎉 Deep Research completado exitosamente!
```

**¿Qué verificar?**
- ✅ WebSocket se conecta correctamente
- ✅ Recibes actualizaciones en tiempo real de cada fase
- ✅ El sistema ejecuta múltiples iteraciones
- ✅ Se identifican gaps de información
- ✅ Se generan queries de refinamiento
- ✅ El reporte final se genera y guarda localmente
- ✅ Las métricas de calidad están presentes

---

### Prueba 3: Verificar Guardado en MongoDB

Si tienes MongoDB configurado:

```bash
# Conectar a MongoDB
docker exec -it aletheia-mongodb mongosh \
  -u aletheia -p aletheia_password \
  --authenticationDatabase admin \
  aletheia

# Dentro de mongosh:

# 1. Ver todas las tareas
db.tasks.find().pretty()

# 2. Ver tareas completadas
db.tasks.find({status: "completed"}).pretty()

# 3. Ver un reporte específico
db.reports.findOne({task_id: "abc-123-def-456"})

# 4. Ver los últimos 5 logs
db.logs.find().sort({timestamp: -1}).limit(5).pretty()

# 5. Contar documentos
db.tasks.countDocuments()
db.reports.countDocuments()
db.logs.countDocuments()
```

**¿Qué verificar?**
- ✅ Las tareas se guardan con task_id, status, query, timestamps
- ✅ Los reportes se guardan con content completo (no "DeepResearchResult(...)")
- ✅ Los logs registran eventos importantes
- ✅ Los datos persisten después de reiniciar la API

---

### Prueba 4: Verificar Trazabilidad

```bash
# 1. Obtener traces de una tarea
TASK_ID="abc-123-def-456"
curl "http://localhost:8000/traces/$TASK_ID" | jq

# 2. Ver logs específicos de una tarea
docker exec -it aletheia-mongodb mongosh \
  -u aletheia -p aletheia_password \
  --authenticationDatabase admin \
  aletheia \
  --eval "db.logs.find({task_id: '$TASK_ID'}).pretty()"
```

**¿Qué verificar?**
- ✅ El endpoint traces responde con manifest, events y otel_export
- ✅ Los logs en MongoDB tienen timestamps correctos
- ✅ Los eventos se registran en orden cronológico

---

## 🐛 Solución de Problemas

### Problema: "API not responding"

```bash
# Verificar que la API esté corriendo
ps aux | grep uvicorn

# Si no está corriendo, iniciar:
uvicorn apps.api.main:app --reload

# Verificar logs:
docker logs aletheia-api  # Si usas Docker
```

### Problema: "WebSocket connection failed"

```bash
# 1. Verificar que websockets esté instalado
pip install websockets==12.0

# 2. Verificar que la API esté corriendo
curl http://localhost:8000/health

# 3. Probar conexión directa
python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://localhost:8000/ws/progress/test'))"
```

### Problema: "Task not found"

Esto ocurre cuando:
1. MongoDB no está configurado y reiniciaste la API (datos en memoria)
2. El task_id es incorrecto

**Solución:**
```bash
# Opción 1: Configurar MongoDB
docker-compose up -d

# Opción 2: Verificar task_id
curl http://localhost:8000/tasks/YOUR_TASK_ID/status
```

### Problema: "Report content is empty or showing object representation"

Esto era el bug que corregimos. Si ves esto:
```json
{
  "content": "DeepResearchResult(original_query=...)"
}
```

**Solución:**
```bash
# Pull los últimos cambios
git pull origin main

# Reiniciar la API
docker-compose restart api  # Si usas Docker
# O
# Ctrl+C y uvicorn apps.api.main:app --reload
```

---

## 📊 Criterios de Éxito

Tu sistema está funcionando correctamente si:

### ✅ Research Simple
- [x] Task ID se genera correctamente
- [x] Status progresa: accepted → running → completed
- [x] Reporte se genera en ~30-60 segundos
- [x] Reporte contiene contenido en Markdown
- [x] Fuentes están documentadas
- [x] Reporte se guarda en MongoDB (si está configurado)

### ✅ Deep Research con WebSocket
- [x] Task ID se genera correctamente
- [x] WebSocket conecta exitosamente
- [x] Eventos se reciben en tiempo real:
  - started
  - planning
  - iteration (múltiples)
  - evidence (múltiples)
  - evaluation (múltiples)
  - gap_analysis
  - refinement
  - report_generation
  - completed
- [x] Reporte final se genera
- [x] Métricas de calidad presentes
- [x] Resumen de investigación presente
- [x] Reporte se guarda en MongoDB con content correcto

### ✅ MongoDB (si está configurado)
- [x] Conexión exitosa
- [x] Collections creadas: tasks, reports, logs
- [x] Tasks guardadas correctamente
- [x] Reports guardados con content completo (no object representation)
- [x] Logs registrados cronológicamente
- [x] Datos persisten después de reiniciar

### ✅ Trazabilidad
- [x] Endpoint /traces responde
- [x] Logs en MongoDB con timestamps
- [x] Eventos en orden cronológico

---

## 🎯 Próximos Pasos

Una vez que todas las pruebas pasen:

1. **Integra en tu aplicación** - Usa la API desde tu código
2. **Personaliza parámetros** - Ajusta iterations, min_score, budget
3. **Configura producción** - Ver [README.md](README.md) sección Deployment
4. **Monitorea** - Usa MongoDB para analizar investigaciones pasadas
5. **Escala** - Deploy en Kubernetes o cloud provider

---

## 📚 Recursos Adicionales

- **[QUICKSTART.md](QUICKSTART.md)** - Guía de inicio para nuevos usuarios
- **[README.md](README.md)** - Documentación completa
- **[API Docs](http://localhost:8000/docs)** - Documentación interactiva de la API
- **[SIMPLIFICATION.md](SIMPLIFICATION.md)** - Detalles de la arquitectura minimalista

---

**¿Algún test falla?** Abre un issue en [GitHub](https://github.com/saptiva-ai/alethia_deepresearch/issues) con:
- Salida del script `python tools/verify_system.py`
- Logs de la API
- Tu configuración de .env (sin las keys)
