import sys
import warnings

# Silenciar advertencias de SSL/urllib3 en macOS
warnings.filterwarnings("ignore")

from core.pipeline import SystemPipelineManager
from agents.orchestrator_agent import LocalNautOrchestrator

def main():
    user_query = sys.argv[1] if len(sys.argv) > 1 else "Hola, ¿en qué me puedes ayudar?"
    
    pipeline = SystemPipelineManager()
    pipeline.ensure_all_services()

    orchestrator = LocalNautOrchestrator()
    final_response = orchestrator.run(user_query)

    print("\n" + "="*20 + " RESPUESTA FINAL " + "="*20 + "\n")
    print(final_response)
    print("\n" + "="*57)

if __name__ == "__main__":
    main()
