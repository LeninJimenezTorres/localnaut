import os

class TaskSession:
    """Mantiene el estado, historial de conversación y contexto de trabajo de la sesión."""
    
    def __init__(self, system_prompt: str = None):
        self.workspace_dir = os.getcwd()
        self.system_prompt = system_prompt or (
            "Eres LocalNaut, un agente CLI autónomo de élite que corre 100% local en macOS.\n\n"
            "HERRAMIENTAS DISPONIBLES:\n"
            "1. search_internet(query=\"...\"): Tienes acceso directo a este buscador web local.\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "- Si el usuario solicita noticias, eventos recientes o información en tiempo real, "
            "debes invocar la herramienta respondiendo únicamente: search_internet(query=\"tu consulta\")\n"
            "- Una vez que se provean los resultados de la búsqueda, responde directamente al usuario en lenguaje natural sintetizando la información."
        )
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_response(self, tool_name: str, result: str):
        self.messages.append({
            "role": "user",
            "content": f"[Resultado de la herramienta '{tool_name}']:\n{result}\n\nCon base en estos resultados, responde a mi consulta inicial."
        })

    def reset(self):
        """Reinicia el historial de la sesión activa."""
        self.messages = [{"role": "system", "content": self.system_prompt}]