#!/usr/bin/env python3
"""
Aletheia Deep Research - Simple Research Example (Python)

Este script demuestra cómo usar la API de Aletheia desde Python
para ejecutar una investigación simple y obtener el reporte.

Uso:
    python examples/simple_research.py "Tu consulta aquí"
"""

import sys
import time
import requests
from datetime import datetime


def check_api_health(api_url: str) -> bool:
    """Verifica que la API esté corriendo"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_research(api_url: str, query: str) -> str:
    """Inicia una investigación y retorna el task_id"""
    response = requests.post(
        f"{api_url}/research",
        json={"query": query},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    return data["task_id"]


def monitor_task(api_url: str, task_id: str, max_attempts: int = 60) -> bool:
    """Monitorea el estado de una tarea hasta que complete o falle"""
    for attempt in range(max_attempts):
        response = requests.get(f"{api_url}/tasks/{task_id}/status", timeout=5)
        response.raise_for_status()

        data = response.json()
        status = data["status"]

        print(f"   Status: {status} (intento {attempt + 1}/{max_attempts})")

        if status == "completed":
            return True
        elif status == "failed":
            print(f"❌ La investigación falló: {data.get('details', 'Unknown error')}")
            return False

        time.sleep(5)

    print("❌ Timeout: La investigación tardó demasiado")
    return False


def get_report(api_url: str, task_id: str) -> dict:
    """Obtiene el reporte final de una investigación"""
    response = requests.get(f"{api_url}/reports/{task_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def save_report(report_md: str, filename: str = None) -> str:
    """Guarda el reporte en un archivo markdown"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_md)

    return filename


def main():
    # Configuration
    API_URL = "http://localhost:8000"
    QUERY = sys.argv[1] if len(sys.argv) > 1 else "Últimas tendencias en inteligencia artificial 2025"

    print("=" * 60)
    print("🔬 Aletheia Deep Research - Simple Example (Python)")
    print("=" * 60)

    # 1. Check API health
    print("\n1️⃣  Verificando que la API esté corriendo...")
    if not check_api_health(API_URL):
        print(f"❌ Error: La API no está corriendo en {API_URL}")
        print("   Inicia con: uvicorn apps.api.main:app --reload")
        sys.exit(1)
    print("✅ API corriendo correctamente")

    # 2. Start research
    print("\n2️⃣  Iniciando investigación...")
    print(f"   Query: {QUERY}")

    try:
        task_id = start_research(API_URL, QUERY)
        print(f"✅ Investigación iniciada")
        print(f"   Task ID: {task_id}")
    except Exception as e:
        print(f"❌ Error al iniciar investigación: {e}")
        sys.exit(1)

    # 3. Monitor progress
    print("\n3️⃣  Monitoreando progreso...")
    if not monitor_task(API_URL, task_id):
        sys.exit(1)
    print("✅ Investigación completada!")

    # 4. Get report
    print("\n4️⃣  Obteniendo reporte...")
    try:
        report_data = get_report(API_URL, task_id)
        report_md = report_data.get("report_md", "")
        sources = report_data.get("sources_bib", "Unknown")

        # Save to file
        filename = save_report(report_md)

        # Display summary
        print("\n" + "=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"Task ID:    {task_id}")
        print(f"Status:     ✅ Completado")
        print(f"Fuentes:    {sources}")
        print(f"Reporte:    {filename}")

        # Preview
        print("\n📄 Preview del reporte:")
        lines = report_md.split("\n")
        for line in lines[:20]:
            print(line)

        if len(lines) > 20:
            print(f"\n... (ver archivo completo: {filename})")

        print("\n🎉 Investigación completada exitosamente!")

    except Exception as e:
        print(f"❌ Error al obtener reporte: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
