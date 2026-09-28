import json
from core.llm_gateway import LocalLLMGateway
from tools.searxng_tool import SearXNGTool
from tools.firecrawl_tool import FirecrawlTool

class LocalNautOrchestrator:
    def __init__(self):
        self.llm = LocalLLMGateway()
        self.search_tool = SearXNGTool()
        self.scrape_tool = FirecrawlTool()
        
        self.tools_schema = [
            self.search_tool.get_schema(),
            self.scrape_tool.get_schema()
        ]
        
        self.system_prompt = {
            "role": "system",
            "content": (
                "Eres LocalNaut, un asistente avanzado de navegación e investigación. "
                "Tienes acceso a herramientas de búsqueda web (SearXNG) y scraping (Firecrawl). "
                "Si el usuario pregunta algo sobre eventos recientes, datos que desconoces o pide investigar, "
                "DEBES usar las herramientas antes de responder. Si ya tienes la respuesta con certeza "
                "absoluta en tu conocimiento interno, responde directamente."
            )
        }

    def execute_task(self, user_query: str) -> str:
        messages = [self.system_prompt, {"role": "user", "content": user_query}]
        
        print("\n[LocalNaut] Analizando la consulta...")
        response_msg = self.llm.generate_response(messages, tools=self.tools_schema)
        
        if response_msg.tool_calls:
            messages.append(response_msg)
            
            for tool_call in response_msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                print(f"[LocalNaut] Ejecutando herramienta: {func_name} con {args}")
                
                if func_name == "search_internet":
                    tool_result = self.search_tool.search(args["query"])
                elif func_name == "scrape_website":
                    tool_result = self.scrape_tool.scrape(args["url"])
                else:
                    tool_result = "Herramienta desconocida."
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": tool_result
                })
            
            print("[LocalNaut] Consolidando información recolectada...")
            final_response = self.llm.generate_response(messages)
            return final_response.content
            
        return response_msg.content
