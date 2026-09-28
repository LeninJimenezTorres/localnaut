import requests

class SearXNGTool:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url

    def search(self, query: str) -> str:
        try:
            res = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json"},
                timeout=10
            )
            res.raise_for_status()
            results = res.json().get("results", [])
            snippets = [f"- {r.get('title')}: {r.get('content')} ({r.get('url')})" for r in results[:5]]
            return "\n".join(snippets) if snippets else "No se encontraron resultados."
        except Exception as e:
            return f"Error en la búsqueda: {str(e)}"

    @staticmethod
    def get_schema():
        return {
            "type": "function",
            "function": {
                "name": "search_internet",
                "description": "Busca información actualizada en internet en tiempo real.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "La consulta de búsqueda."}
                    },
                    "required": ["query"]
                }
            }
        }
