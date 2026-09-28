import requests

def search_internet(query: str, searxng_url: str = "http://localhost:8080") -> str:
    """Realiza una búsqueda web local utilizando SearXNG y devuelve los resultados formateados."""
    try:
        response = requests.get(
            f"{searxng_url}/search",
            params={"q": query, "format": "json"},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])[:5]
            
            if not results:
                return "No se encontraron resultados web relevantes para esta búsqueda."
            
            summary = []
            for idx, r in enumerate(results, 1):
                title = r.get("title", "Sin título")
                snippet = r.get("content", "Sin descripción")
                url = r.get("url", "")
                summary.append(f"[{idx}] Título: {title}\n    URL: {url}\n    Resumen: {snippet}\n")
            
            return "\n".join(summary)
        else:
            return f"Error HTTP {response.status_code} al consultar SearXNG: {response.text[:200]}"
            
    except Exception as e:
        return f"Excepción al conectar con el buscador local SearXNG: {str(e)}"
