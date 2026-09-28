from openai import OpenAI

class LocalLLMGateway:
    """Pasarela de comunicación con el modelo LLM local (Ollama) vía interfaz compatible con OpenAI."""
    
    def __init__(self, base_url="http://localhost:11434/v1", model_name="qwen2.5-coder:14b"):
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model_name = model_name

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """Envía una lista de mensajes al modelo local y retorna el contenido de la respuesta."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error de comunicación con Ollama: {str(e)}"
