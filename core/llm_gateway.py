from openai import OpenAI

class LocalLLMGateway:
    """LocalNaut LLM Gateway - Encapsulates local inference via Ollama."""
    def __init__(self, model_name="qwen2.5-coder:14b", base_url="http://localhost:11434/v1"):
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model_name = model_name

    def generate_response(self, messages, tools=None):
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message
