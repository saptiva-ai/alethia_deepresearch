#!/usr/bin/env python3
"""
Test script to verify API keys are working
Comprehensive test suite for Aletheia Deep Research APIs
"""
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_env_vars():
    """Verifica que las variables de entorno estén configuradas correctamente"""
    print("=== Testing Environment Variables ===")
    saptiva_key = os.getenv("SAPTIVA_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    saptiva_url = os.getenv("SAPTIVA_BASE_URL", "https://api.saptiva.com/v1")

    print(f"SAPTIVA_API_KEY: {'✅ Set' if saptiva_key and saptiva_key != 'pon_tu_api_key_aqui' and saptiva_key != 'your_saptiva_api_key_here' else '❌ Not set'}")
    print(f"TAVILY_API_KEY: {'✅ Set' if tavily_key and tavily_key != 'pon_tu_api_key_aqui' and tavily_key != 'your_tavily_api_key_here' else '❌ Not set'}")
    print(f"SAPTIVA_BASE_URL: {saptiva_url}")

    # Validate Saptiva URL
    if saptiva_url and 'saptiva.ai' in saptiva_url:
        print("⚠️  WARNING: SAPTIVA_BASE_URL contiene 'saptiva.ai' - debe ser 'saptiva.com'")

    return saptiva_key, tavily_key, saptiva_url


def test_tavily_api(api_key):
    """Prueba la conexión y funcionalidad de Tavily API"""
    print("\n=== Testing Tavily API ===")

    # Validar API key
    if not api_key or api_key in ["pon_tu_api_key_aqui", "your_tavily_api_key_here"]:
        print("❌ Tavily API key not configured")
        return False

    try:
        from tavily import TavilyClient

        print("🔄 Conectando a Tavily...")
        start_time = time.time()
        client = TavilyClient(api_key=api_key)

        # Test básico de búsqueda
        print("🔍 Ejecutando búsqueda de prueba...")
        response = client.search(
            query="AI technology trends 2025",
            search_depth="basic",
            max_results=3
        )

        elapsed_time = time.time() - start_time
        results = response.get("results", [])

        print(f"✅ Tavily API working! Found {len(results)} results in {elapsed_time:.2f}s")

        # Mostrar primeros resultados
        for i, result in enumerate(results[:2]):
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            print(f"  [{i+1}] {title[:60]}...")
            print(f"      URL: {url[:80]}")

        return True

    except ImportError:
        print("❌ Error: Librería 'tavily-python' no instalada")
        print("   Instala con: pip install tavily-python")
        return False
    except Exception as e:
        print(f"❌ Tavily API error: {type(e).__name__}: {e}")
        return False


def test_saptiva_api(api_key, base_url=None):
    """Prueba la conexión y funcionalidad de Saptiva API"""
    print("\n=== Testing Saptiva API ===")

    # Validar API key
    if not api_key or api_key in ["pon_tu_api_key_aqui", "your_saptiva_api_key_here"]:
        print("❌ Saptiva API key not configured")
        return False

    # Usar URL de environment o default correcto
    if not base_url:
        base_url = os.getenv("SAPTIVA_BASE_URL", "https://api.saptiva.com/v1")

    try:
        import requests

        print(f"🔄 Conectando a Saptiva API: {base_url}")
        print(f"   API Key: {api_key[:20]}...")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Test con diferentes modelos
        test_models = ["Saptiva Turbo", "SAPTIVA_OPS"]

        for model in test_models:
            print(f"\n📊 Testing model: {model}")
            start_time = time.time()

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Responde en español: ¿Qué es inteligencia artificial?"}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }

            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                print(f"✅ {model} working! ({elapsed_time:.2f}s)")
                data = response.json()

                # Extraer respuesta
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})

                print(f"   Response preview: {content[:80]}...")
                print(f"   Tokens: prompt={usage.get('prompt_tokens', 0)}, "
                      f"completion={usage.get('completion_tokens', 0)}, "
                      f"total={usage.get('total_tokens', 0)}")

                # Solo necesitamos que un modelo funcione
                return True
            else:
                print(f"❌ {model} error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")

        print("\n❌ Ningún modelo de Saptiva funcionó correctamente")
        return False

    except requests.exceptions.Timeout:
        print("❌ Timeout: La API de Saptiva no respondió a tiempo")
        print("   Intenta aumentar SAPTIVA_READ_TIMEOUT en .env")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se pudo conectar a la API de Saptiva")
        print("   Verifica tu conexión a internet y el SAPTIVA_BASE_URL")
        return False
    except Exception as e:
        print(f"❌ Saptiva API error: {type(e).__name__}: {e}")
        return False


def test_api_health_endpoint():
    """Prueba el endpoint /health de la API local"""
    print("\n=== Testing Local API Health Endpoint ===")

    try:
        import requests

        print("🔄 Checking http://localhost:8000/health...")
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health check passed!")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   APIs available: {data.get('api_keys')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("⚠️  API no está corriendo en http://localhost:8000")
        print("   Inicia con: uvicorn apps.api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Aletheia Deep Research - API Test Suite")
    print("=" * 60)

    # Test environment variables
    saptiva_key, tavily_key, saptiva_url = test_env_vars()

    # Test APIs
    tavily_ok = test_tavily_api(tavily_key)
    saptiva_ok = test_saptiva_api(saptiva_key, saptiva_url)
    health_ok = test_api_health_endpoint()

    # Summary
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)

    print(f"✓ Environment Variables: {'✅ Configured' if saptiva_key and tavily_key else '❌ Missing'}")
    print(f"✓ Tavily Search API:     {'✅ Working' if tavily_ok else '❌ Not working'}")
    print(f"✓ Saptiva Model API:     {'✅ Working' if saptiva_ok else '❌ Not working'}")
    print(f"✓ Local API Server:      {'✅ Running' if health_ok else '⚠️  Not running'}")

    # Exit code
    all_ok = tavily_ok and saptiva_ok

    if all_ok:
        print("\n" + "=" * 60)
        print("🎉 TODAS LAS PRUEBAS PASARON!")
        print("=" * 60)
        print("\n✅ Sistema listo para ejecutar investigaciones")
        print("   Prueba con: curl -X POST http://localhost:8000/research \\")
        print('              -H "Content-Type: application/json" \\')
        print('              -d \'{"query": "Tu consulta aquí"}\'')
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("⚠️  ALGUNAS PRUEBAS FALLARON")
        print("=" * 60)
        print("\n🔧 Pasos de resolución:")

        if not saptiva_ok:
            print("\n  1. Verifica tu SAPTIVA_API_KEY en .env")
            print("     - Obtén tu key en: https://lab.saptiva.com/")
            print("     - Asegúrate de usar https://api.saptiva.com (NO .ai)")

        if not tavily_ok:
            print("\n  2. Verifica tu TAVILY_API_KEY en .env")
            print("     - Obtén tu key en: https://tavily.com")
            print("     - Asegúrate de tener créditos disponibles")

        if not health_ok:
            print("\n  3. Inicia el servidor API:")
            print("     uvicorn apps.api.main:app --reload")

        print("\n  Para más ayuda, revisa el README.md")
        sys.exit(1)
