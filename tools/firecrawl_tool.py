import requests

class FirecrawlTool:
    def __init__(self, base_url="http://localhost:3002"):
        self.base_url = base_url

    def scrape(self, url: str) -> str:
        try:
            res = requests.post(
                f"{self.base_url}/v0/scrape",
                json={"url": url},
                timeout=15
            )
            res.raise_for_status()
            data = res.json()
            return data.get("data", {}).get("content", "No se pudo extraer contenido.")[:4000]
        except Exception as e:
            return f"Error al hacer scraping: {str(e)}"

    @staticmethod
    def get_schema():
        return {
            "type": "function",
            "function": {
                "name": "scrape_website",
                "description": "Extrae el texto completo de una URL específica.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "La URL a analizar."}
                    },
                    "required": ["url"]
                }
            }
        }
