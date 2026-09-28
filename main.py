import sys
import argparse
from agents.orchestrator_agent import LocalNautOrchestrator

def main():
    parser = argparse.ArgumentParser(description="LocalNaut - AI Browser Agent CLI")
    parser.add_argument("query", type=str, help="La consulta o tarea para LocalNaut.")
    args = parser.parse_args()

    orchestrator = LocalNautOrchestrator()
    try:
        resultado = orchestrator.execute_task(args.query)
        print("\n=== LOCALNAUT RESPUESTA FINAL ===")
        print(resultado)
    except Exception as e:
        print(f"\n[Error] Fallo en la ejecución de LocalNaut: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
