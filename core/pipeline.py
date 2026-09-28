import subprocess
import time
import sys
import shutil
import os
import requests

class SystemPipelineManager:
    """Gestiona e instala automáticamente toda la infraestructura local requerida en macOS."""
    
    def __init__(self, model_name="qwen2.5-coder:14b", searxng_port=8080, firecrawl_port=3002, ollama_port=11434):
        self.model_name = model_name
        self.searxng_url = f"http://localhost:{searxng_port}"
        self.firecrawl_url = f"http://localhost:{firecrawl_port}"
        self.ollama_url = f"http://localhost:{ollama_port}"

    def _find_ollama_cmd(self):
        cmd = shutil.which("ollama")
        if cmd:
            return cmd
        candidates = ["/opt/homebrew/bin/ollama", "/usr/local/bin/ollama", "/usr/bin/ollama"]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return None

    def _find_docker_cmd(self):
        cmd = shutil.which("docker")
        if cmd:
            return cmd
        candidates = [
            "/opt/homebrew/bin/docker",
            "/usr/local/bin/docker",
            "/Applications/Docker.app/Contents/Resources/bin/docker",
            os.path.expanduser("~/.docker/bin/docker")
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return None

    def _wait_for_service(self, url, timeout=15):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                res = requests.get(url, timeout=2)
                if res.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def ensure_all_services(self):
        print("\n[Pipeline] 🔍 Verificando estado de la infraestructura local...")
        self._ensure_ollama_and_model()
        self._ensure_searxng_container()
        self._ensure_firecrawl_container()
        print("[Pipeline] ✅ Toda la infraestructura está lista y operativa.\n")

    def _ensure_ollama_and_model(self):
        if not self._wait_for_service(f"{self.ollama_url}/api/tags", timeout=2):
            ollama_bin = self._find_ollama_cmd()
            has_app = os.path.exists("/Applications/Ollama.app")

            print("[Pipeline] ⚠️ Iniciando servicio Ollama en segundo plano...")
            if ollama_bin:
                subprocess.Popen([ollama_bin, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif has_app:
                subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if not self._wait_for_service(f"{self.ollama_url}/api/tags", timeout=20):
                print("[Pipeline] ❌ No se pudo conectar con Ollama.")
                sys.exit(1)

        try:
            res = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            models = [m.get("name") for m in res.json().get("models", [])]
            if not any(self.model_name in m for m in models):
                print(f"[Pipeline] ⏳ Modelo '{self.model_name}' no presente. Descargando automáticamente...")
                ollama_bin = self._find_ollama_cmd() or "ollama"
                subprocess.run([ollama_bin, "pull", self.model_name], check=True)
                print(f"[Pipeline] ✅ Modelo '{self.model_name}' descargado y listo.")
            else:
                print(f"[Pipeline] ✔️ Ollama y modelo '{self.model_name}' listos.")
        except Exception as e:
            print(f"[Pipeline] ❌ Error al verificar modelo en Ollama: {e}")
            sys.exit(1)

    def _ensure_searxng_container(self):
        # Comprobar si SearXNG ya está respondiendo a consultas JSON
        if self._wait_for_service(f"{self.searxng_url}/search?q=ping&format=json", timeout=2):
            print("[Pipeline] ✔️ SearXNG corriendo con soporte JSON activo en puerto 8080.")
            return

        docker_bin = self._find_docker_cmd() or "docker"
        settings_path = os.path.abspath("searxng/settings.yml")

        print("[Pipeline] ⚙️ Reconfigurando contenedor SearXNG con soporte JSON...")
        try:
            # Eliminar contenedor previo si existía sin soporte JSON
            subprocess.run([docker_bin, "rm", "-f", "searxng"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Lanzar SearXNG con el volumen de configuración montado
            subprocess.run([
                docker_bin, "run", "-d",
                "-p", "8080:8080",
                "-v", f"{settings_path}:/etc/searxng/settings.yml",
                "--name", "searxng",
                "searxng/searxng"
            ], check=True, stdout=subprocess.DEVNULL)
            
            if self._wait_for_service(f"{self.searxng_url}/search?q=ping&format=json", timeout=15):
                print("[Pipeline] ✅ SearXNG desplegado y verificado con soporte JSON.")
            else:
                print("[Pipeline] ⚠️ SearXNG desplegado pero aún inicializando...")
        except Exception as e:
            print(f"[Pipeline] ⚠️ Error al desplegar SearXNG: {e}")

    def _ensure_firecrawl_container(self):
        if self._wait_for_service(f"{self.firecrawl_url}/is-healthy", timeout=2):
            print("[Pipeline] ✔️ Firecrawl activo en puerto 3002.")
            return
        print("[Pipeline] ℹ️ Firecrawl no detectado en puerto 3002 (Opcional).")
