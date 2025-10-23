#!/usr/bin/env python3
"""
Aletheia Deep Research - Deep Research Example (Python)

Este script demuestra cómo usar la API de Deep Research para investigaciones
profundas e iterativas con evaluación de calidad.

Características:
- Refinamiento iterativo automático
- Evaluación de completitud
- Gap analysis
- Métricas de calidad detalladas

Uso:
    python examples/deep_research.py "Tu consulta compleja aquí"
    python examples/deep_research.py --iterations 5 --min-score 0.9 "Tu consulta"
"""

import argparse
import asyncio
from datetime import datetime
import json
import sys
import time

import requests
import websockets


class DeepResearchClient:
    """Cliente para la API de Deep Research"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def check_health(self) -> bool:
        """Verifica que la API esté corriendo"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def start_deep_research(
        self,
        query: str,
        max_iterations: int = 3,
        min_completion_score: float = 0.75,
        budget: int = 100
    ) -> str:
        """Inicia una investigación profunda"""
        payload = {
            "query": query,
            "max_iterations": max_iterations,
            "min_completion_score": min_completion_score,
            "budget": budget
        }

        response = requests.post(
            f"{self.api_url}/deep-research",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data["task_id"]

    def get_status(self, task_id: str) -> dict:
        """Obtiene el estado de una tarea"""
        response = requests.get(
            f"{self.api_url}/deep-research/{task_id}",
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    def monitor_research(self, task_id: str, max_wait_minutes: int = 10) -> dict | None:
        """Monitorea el progreso de una investigación profunda (método legacy sin WebSocket)"""
        max_attempts = max_wait_minutes * 12  # Check every 5 seconds
        start_time = time.time()

        for attempt in range(max_attempts):
            try:
                data = self.get_status(task_id)
                status = data.get("status")

                elapsed = time.time() - start_time
                print(f"   [{elapsed:.1f}s] Status: {status} (intento {attempt + 1}/{max_attempts})")

                if status == "completed":
                    return data
                elif status == "failed":
                    error = data.get("report_md", "Unknown error")
                    print(f"❌ La investigación falló: {error}")
                    return None

                time.sleep(5)

            except Exception as e:
                print(f"⚠️  Error al verificar estado: {e}")
                time.sleep(5)

        print("❌ Timeout: La investigación tardó demasiado")
        return None

    async def monitor_research_websocket(self, task_id: str, max_wait_minutes: int = 10) -> dict | None:
        """
        Monitorea el progreso de una investigación profunda usando WebSocket para actualizaciones en tiempo real.

        Returns:
            El resultado final de la investigación o None si falla
        """
        # Convert http:// to ws://
        ws_url = self.api_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_endpoint = f"{ws_url}/ws/progress/{task_id}"

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60

        print(f"   📡 Conectando a WebSocket: {ws_endpoint}")

        try:
            async with websockets.connect(ws_endpoint, ping_interval=20, ping_timeout=10) as websocket:
                print("   ✅ WebSocket conectado - recibiendo actualizaciones en tiempo real\n")

                while True:
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > max_wait_seconds:
                        print(f"\n❌ Timeout: La investigación tardó más de {max_wait_minutes} minutos")
                        return None

                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        update = json.loads(message)

                        # Format and display the update
                        event_type = update.get("event_type", "unknown")
                        message_text = update.get("message", "")
                        timestamp = update.get("timestamp")
                        data = update.get("data", {})

                        # Display with emoji based on event type
                        emoji_map = {
                            "started": "🚀",
                            "planning": "📋",
                            "iteration": "🔄",
                            "evidence": "🔍",
                            "evaluation": "📊",
                            "gap_analysis": "🎯",
                            "refinement": "🔧",
                            "report_generation": "📝",
                            "completed": "✅",
                            "failed": "❌",
                        }
                        emoji = emoji_map.get(event_type, "ℹ️")

                        time_context = f"{elapsed:.1f}s"
                        if timestamp:
                            time_context = f"{time_context} | {timestamp}"

                        print(f"   {emoji} [{time_context}] {message_text}")

                        # Show additional data for some events
                        if event_type == "evaluation" and data:
                            score = data.get("score", 0)
                            print(f"      └─ Score: {score:.2%}")

                        if event_type == "gap_analysis" and data:
                            gaps = data.get("gaps", [])
                            if gaps:
                                gap_types = ", ".join(g.get("type", "") for g in gaps[:2])
                                print(f"      └─ Top gaps: {gap_types}")

                        # Check if completed or failed
                        if event_type == "completed":
                            print(f"\n✅ Investigación completada en {elapsed:.1f}s")
                            # Get final result
                            return self.get_status(task_id)

                        elif event_type == "failed":
                            error = data.get("error", "Unknown error")
                            print(f"\n❌ La investigación falló: {error}")
                            return None

                    except TimeoutError:
                        # No message in 30s, send ping
                        await websocket.send("ping")
                        continue

        except websockets.exceptions.WebSocketException as e:
            print(f"\n⚠️  Error de WebSocket: {e}")
            print("   Volviendo a polling tradicional...")
            return self.monitor_research(task_id, max_wait_minutes)

        except Exception as e:
            print(f"\n⚠️  Error inesperado: {e}")
            return None


def format_quality_metrics(metrics: dict) -> str:
    """Formatea las métricas de calidad para mostrar"""
    lines = []
    lines.append("📊 Métricas de Calidad:")
    lines.append(f"   • Completion Level:  {metrics.get('completion_level', 0):.2%}")
    lines.append(f"   • Quality Score:     {metrics.get('quality_score', 0):.2%}")
    lines.append(f"   • Evidence Count:    {metrics.get('evidence_count', 0)}")
    lines.append(f"   • Execution Time:    {metrics.get('execution_time', 0):.1f}s")
    return "\n".join(lines)


def format_research_summary(summary: dict) -> str:
    """Formatea el resumen de investigación"""
    lines = []
    lines.append("📋 Resumen de Investigación:")
    lines.append(f"   • Iteraciones:       {summary.get('iterations_completed', 0)}")

    gaps = summary.get("gaps_identified", [])
    if gaps:
        lines.append(f"   • Brechas:           {', '.join(gaps[:3])}")

    findings = summary.get("key_findings", [])
    if findings:
        lines.append("   • Hallazgos clave:")
        for finding in findings[:3]:
            lines.append(f"     - {finding}")

    return "\n".join(lines)


def save_report(report_md: str, query: str) -> str:
    """Guarda el reporte en un archivo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize query for filename
    safe_query = "".join(c for c in query[:30] if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_query = safe_query.replace(" ", "_")
    filename = f"deep_research_{safe_query}_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_md)

    return filename


async def async_main():
    """Función asíncrona principal que usa WebSocket para monitoreo en tiempo real."""
    parser = argparse.ArgumentParser(
        description="Aletheia Deep Research - Deep Research Example with WebSocket"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Impacto de la inteligencia artificial en el mercado laboral latinoamericano",
        help="Consulta de investigación"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Número máximo de iteraciones (1-10)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.85,
        help="Score mínimo de completitud (0.1-1.0)"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=200,
        help="Presupuesto total para la investigación"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL de la API"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🔬 Aletheia Deep Research - Deep Research Example")
    print("=" * 70)

    # Initialize client
    client = DeepResearchClient(args.api_url)

    # 1. Check API health
    print("\n1️⃣  Verificando API...")
    if not client.check_health():
        print(f"❌ Error: La API no está corriendo en {args.api_url}")
        print("   Inicia con: uvicorn apps.api.main:app --reload")
        sys.exit(1)
    print("✅ API disponible")

    # 2. Start deep research
    print("\n2️⃣  Iniciando Deep Research...")
    print(f"   Query:              {args.query}")
    print(f"   Max Iterations:     {args.iterations}")
    print(f"   Min Completion:     {args.min_score:.0%}")
    print(f"   Budget:             {args.budget}")

    try:
        task_id = client.start_deep_research(
            query=args.query,
            max_iterations=args.iterations,
            min_completion_score=args.min_score,
            budget=args.budget
        )
        print("\n✅ Deep Research iniciado")
        print(f"   Task ID: {task_id}")
    except Exception as e:
        print(f"❌ Error al iniciar: {e}")
        sys.exit(1)

    # 3. Monitor progress with WebSocket
    print("\n3️⃣  Monitoreando progreso en tiempo real (esto puede tomar varios minutos)...")
    print("   📡 Usando WebSocket para actualizaciones instantáneas... (Ctrl+C para cancelar)\n")

    result = await client.monitor_research_websocket(task_id, max_wait_minutes=10)

    if not result:
        sys.exit(1)

    print("\n✅ Deep Research completado!")

    # 4. Display results
    print("\n4️⃣  Resultados:")
    print("=" * 70)

    # Quality metrics
    if "quality_metrics" in result and result["quality_metrics"]:
        print("\n" + format_quality_metrics(result["quality_metrics"]))

    # Research summary
    if "research_summary" in result and result["research_summary"]:
        print("\n" + format_research_summary(result["research_summary"]))

    # Save report
    report_md = result.get("report_md", "")
    if report_md:
        filename = save_report(report_md, args.query)
        print(f"\n💾 Reporte guardado en: {filename}")

        # Preview
        print("\n📄 Preview del reporte:")
        lines = report_md.split("\n")
        for line in lines[:15]:
            print(line)
        if len(lines) > 15:
            print(f"\n... (ver archivo completo: {filename})")

    print("\n" + "=" * 70)
    print("🎉 Deep Research completado exitosamente!")
    print("=" * 70)


def main():
    """Wrapper síncrono para ejecutar la función asíncrona."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
