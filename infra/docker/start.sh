#!/bin/bash
# Aletheia Docker Startup Script

set -e

echo "🚀 Starting Aletheia Deep Research Services..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.docker .env
    echo "⚠️  Please edit .env file with your API keys before running:"
    echo "   - SAPTIVA_API_KEY"
    echo "   - TAVILY_API_KEY"
    echo ""
    echo "Then run: docker-compose up -d"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🔧 Pulling latest images..."
docker-compose pull

echo "🏗️  Building Aletheia application..."
docker-compose build aletheia-api

echo "🌟 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ Aletheia Deep Research is running!"
echo ""
echo "📊 Service URLs:"
echo "   • API:         http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
echo "   • Jaeger UI:   http://localhost:16686"
echo "   • Weaviate:    http://localhost:8080"
echo "   • MinIO:       http://localhost:9001 (admin/minioadmin123)"
echo ""
echo "🧪 Test the API:"
echo '   curl -X POST "http://localhost:8000/research" -H "Content-Type: application/json" -d '\''{"query": "Test research query"}'\'''
echo ""
echo "📜 View logs: docker-compose logs -f aletheia-api"
echo "🛑 Stop all:  docker-compose down"