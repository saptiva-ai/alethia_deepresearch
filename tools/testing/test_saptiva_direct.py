#!/usr/bin/env python3
"""
Test directo de integración con Saptiva API
Este script verifica la conexión y autenticación con Saptiva fuera del stack principal
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def test_saptiva_api():
    """Test directo de la API de Saptiva"""
    api_key = os.getenv("SAPTIVA_API_KEY")

    if not api_key:
        print("❌ ERROR: SAPTIVA_API_KEY no encontrada en .env")
        return False

    print(f"✅ API Key encontrada: {api_key[:20]}...")

    # Configuración según documentación oficial
    url = "https://api.saptiva.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Payload de prueba simple
    payload = {
        "model": "Saptiva Turbo",
        "messages": [{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "Say hello in Spanish"}],
        "max_tokens": 100,
        "temperature": 0.7,
    }

    print(f"🔄 Probando conexión a: {url}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def test_alternative_models():
    """Test diferentes modelos disponibles"""
    models = ["Saptiva Turbo", "Saptiva Cortex", "Saptiva Ops"]

    for model in models:
        print(f"\n🧪 Testing model: {model}")
        # Test básico para cada modelo
        # (implementación simplificada)


if __name__ == "__main__":
    print("🚀 Iniciando test directo de Saptiva API...")
    print("=" * 50)

    success = test_saptiva_api()

    if success:
        print("\n🎉 Integración Saptiva funcionando correctamente!")
    else:
        print("\n💥 Problemas con la integración Saptiva")
        print("\n🔍 Verificaciones sugeridas:")
        print("1. API Key válida en .env")
        print("2. Conexión a internet")
        print("3. Endpoint correcto: https://api.saptiva.com/v1/chat/completions")
        print("4. Cuenta activa en https://lab.saptiva.com/")
