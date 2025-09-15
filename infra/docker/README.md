# 🐳 Aletheia Docker Setup

## 🚀 Quick Start

### 1. **Configure Environment**
```bash
cd infra/docker
cp .env.docker .env
# Edit .env with your API keys
```

### 2. **Start Services (Automated)**
```bash
# Uses the startup script
./start.sh
```

### 3. **Start Services (Manual)**
```bash
# Option A: All services including API
docker-compose up -d

# Option B: External services only (for local development)
docker-compose -f docker-compose.minimal.yml up -d
```

---

## 📊 **Services Available**

### **Essential Services:**
- **🔍 Jaeger UI**: http://localhost:16686 - Distributed tracing
- **🧠 Weaviate**: http://localhost:8080 - Vector database  
- **📦 MinIO**: http://localhost:9001 - Object storage (admin/minioadmin123)
- **🚀 Aletheia API**: http://localhost:8000 - Main application
- **📖 API Docs**: http://localhost:8000/docs - Interactive API documentation

---

## 🧪 **Testing the Setup**

### **1. Health Check**
```bash
curl http://localhost:8000/health
```

### **2. Research API Test**
```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Banking analysis in Mexico 2024"}'
```

### **3. Deep Research Test**
```bash
curl -X POST "http://localhost:8000/deep-research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Fintech market analysis Mexico 2024",
    "max_iterations": 2,
    "min_completion_score": 0.7
  }'
```

---

## 🔧 **Management Commands**

### **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f aletheia-api
docker-compose logs -f weaviate
docker-compose logs -f jaeger
```

### **Service Status**
```bash
docker-compose ps
```

### **Stop Services**
```bash
# Stop but keep data
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

### **Restart Services**
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart aletheia-api
```

---

## 🛠️ **Development Modes**

### **Mode 1: Full Stack (Production-like)**
```bash
docker-compose up -d
```
- ✅ All services in containers
- ✅ Complete isolation
- ✅ Production-like environment

### **Mode 2: External Services Only**
```bash
docker-compose -f docker-compose.minimal.yml up -d
# Then run API locally:
cd ../../
uvicorn apps.api.main:app --reload
```
- ✅ Fast development cycles
- ✅ Easy debugging
- ✅ External services in containers

---

## 📁 **Volume Mounts**

- **Weaviate Data**: `./weaviate_data` → `/var/lib/weaviate`
- **MinIO Data**: `./minio_data` → `/data`
- **Application Runs**: `../../runs` → `/app/runs`
- **Prompts**: `../../prompts` → `/app/prompts` (read-only)

---

## 🔍 **Troubleshooting**

### **Port Conflicts**
If ports are already in use, modify the docker-compose.yml port mappings:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### **Permission Issues**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 weaviate_data minio_data
```

### **Service Won't Start**
```bash
# Check specific service logs
docker-compose logs service-name

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Reset Everything**
```bash
# Nuclear option - removes all data
docker-compose down -v
docker system prune -f
./start.sh
```

---

## 🌐 **Network Configuration**

All services run on the `aletheia-network` bridge network, allowing internal communication using service names:

- `weaviate:8080` - From API container
- `minio:9000` - From API container  
- `jaeger:4317` - From API container

---

## 📝 **Required Environment Variables**

```bash
# Core API Keys (REQUIRED)
SAPTIVA_API_KEY=your_saptiva_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Auto-configured by Docker Compose
WEAVIATE_HOST=http://weaviate:8080
MINIO_ENDPOINT=minio:9000
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```