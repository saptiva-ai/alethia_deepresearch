#!/usr/bin/env python3
"""
Test script to verify API keys are working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_env_vars():
    print("=== Testing Environment Variables ===")
    saptiva_key = os.getenv("SAPTIVA_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    print(f"SAPTIVA_API_KEY: {'✅ Set' if saptiva_key and saptiva_key != 'pon_tu_api_key_aqui' else '❌ Not set'}")
    print(f"TAVILY_API_KEY: {'✅ Set' if tavily_key and tavily_key != 'pon_tu_api_key_aqui' else '❌ Not set'}")

    return saptiva_key, tavily_key


def test_tavily_api(api_key):
    print("\n=== Testing Tavily API ===")
    if not api_key or api_key == "pon_tu_api_key_aqui":
        print("❌ Tavily API key not configured")
        return False

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)

        # Simple test search
        response = client.search(query="Mexico fintech news 2024", search_depth="basic", max_results=2)
        results = response.get("results", [])

        print(f"✅ Tavily API working! Found {len(results)} results")
        for i, result in enumerate(results[:1]):  # Show first result
            print(f"  - {result.get('title', 'No title')[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Tavily API error: {e}")
        return False


def test_saptiva_api(api_key):
    print("\n=== Testing Saptiva API ===")
    if not api_key or api_key == "pon_tu_api_key_aqui":
        print("❌ Saptiva API key not configured")
        return False

    try:
        import requests

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {"model": "SAPTIVA_OPS", "messages": [{"role": "user", "content": "Test: ¿Qué es fintech?"}], "max_tokens": 100, "temperature": 0.7}

        response = requests.post("https://api.saptiva.ai/v1/chat/completions", headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Saptiva API working!")
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  Response: {content[:100]}...")
            return True
        else:
            print(f"❌ Saptiva API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Saptiva API error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 API Test Suite\n")

    saptiva_key, tavily_key = test_env_vars()

    tavily_ok = test_tavily_api(tavily_key)
    saptiva_ok = test_saptiva_api(saptiva_key)

    print("\n=== Summary ===")
    print(f"Tavily API: {'✅ Ready' if tavily_ok else '❌ Not working'}")
    print(f"Saptiva API: {'✅ Ready' if saptiva_ok else '❌ Not working'}")

    if tavily_ok and saptiva_ok:
        print("\n🎉 All APIs ready for Deep Research!")
    else:
        print("\n⚠️  Some APIs need attention before Deep Research can work fully.")
