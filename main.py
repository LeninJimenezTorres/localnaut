import sys
import argparse
from core.pipeline import SystemPipelineManager
from agents.orchestrator_agent import LocalNautOrchestrator

def main():
    parser = argparse.ArgumentParser(description="LocalNaut - Autonomous AI Browser Agent")
    parser.add_argument("query", type=str, help="Consulta o instrucción para LocalNaut.")
    args = parser.parse_args()

    # 1. Ejecutar Pipeline de Auto-bootstrap e Infraestructura
    pipeline = SystemPipelineManager()
    pipeline.ensure_all_services()

    # 2. Ejecutar Agente Orquestador
    orchestrator = LocalNautOrchestrator()
    try:
        resultado = orchestrator.execute_task(args.query)
        print("\n=== LOCALNAUT RESPUESTA FINAL ===")
        print(resultado)
    except Exception as e:
        print(f"\n[Error] Fallo en la ejecución del agente: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
