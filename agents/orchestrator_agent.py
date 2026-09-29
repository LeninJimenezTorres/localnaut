import json
import re
from core.llm_gateway import LocalLLMGateway
from tools.search_tool import search_internet

class LocalNautOrchestrator:
    """Orquestador de agentes con memoria de sesión y llamadas a herramientas."""
    
    def __init__(self):
        self.llm = LocalLLMGateway()

    def process_turn(self, session, user_input: str, status_callback=None) -> str:
        session.add_user_message(user_input)

        if status_callback:
            status_callback("🧠 Analizando consulta e intenciones...")

        # Primera evaluación del modelo
        response = self.llm.chat(session.messages)

        # Detectar si el modelo solicitó una búsqueda web
        search_match = re.search(r'search_internet\((?:query=)?["\'](.*?)["\']\)', response) or \
                       re.search(r'\{\s*"name":\s*"search_internet",\s*"arguments":\s*\{\s*"query":\s*"(.*?)"\s*\}\s*\}', response)

        if search_match:
            query = search_match.group(1)

            # Guardar la invocación del asistente en el historial
            session.add_assistant_message(response)

            if status_callback:
                status_callback(f"🌐 Consultando SearXNG local: '{query}'...")

            # Ejecutar búsqueda en SearXNG
            search_results = search_internet(query)

            # Inyectar el resultado en la sesión
            session.add_tool_response("search_internet", search_results)

            if status_callback:
                status_callback("📝 Sintetizando respuesta con datos web...")

            # Generar la respuesta final sintetizada
            response = self.llm.chat(session.messages)

        session.add_assistant_message(response)
        return response