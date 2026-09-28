import json
from core.llm_gateway import LocalLLMGateway
from tools.search_tool import search_internet

class LocalNautOrchestrator:
    """Orquestador con bucle completo de ejecución de herramientas."""
    
    def __init__(self):
        self.llm = LocalLLMGateway()

    def run(self, user_prompt: str) -> str:
        print("\n[LocalNaut] 🧠 Analizando la consulta e identificando intención...")
        
        system_prompt = (
            "Eres LocalNaut, un asistente de IA avanzado y local. "
            "Tienes acceso a la herramienta 'search_internet(query)'. "
            "Si la consulta del usuario requiere información actualizada o búsquedas en la web, "
            "DEBES responder EXCLUSIVAMENTE con un JSON con el siguiente formato estricto:\n"
            '{"name": "search_internet", "arguments": {"query": "<busqueda>"}}\n\n'
            "Si NO requieres búsqueda web, responde directamente al usuario en texto plano."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response_content = self.llm.chat(messages)

        # Intentar detectar si el modelo devolvió una llamada a herramienta
        try:
            cleaned_response = response_content.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
            
            action = json.loads(cleaned_response)
            if isinstance(action, dict) and action.get("name") == "search_internet":
                search_query = action.get("arguments", {}).get("query", user_prompt)
                
                print(f"[LocalNaut] 🌐 Ejecutando búsqueda local en SearXNG: '{search_query}'...")
                search_results = search_internet(search_query)

                print("[LocalNaut] 📝 Sintetizando y redactando respuesta final...")
                synthesis_messages = [
                    {"role": "system", "content": "Eres un asistente experto. Resume y responde a la solicitud del usuario utilizando ÚNICAMENTE la siguiente información extraída de internet de forma clara, profesional y estructurada en español."},
                    {"role": "user", "content": f"Solicitud original: {user_prompt}\n\nResultados de la búsqueda web:\n{search_results}"}
                ]
                return self.llm.chat(synthesis_messages)
        except (json.JSONDecodeError, AttributeError):
            pass

        return response_content
