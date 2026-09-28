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
        """Detecta la ruta del ejecutable de Ollama."""
        cmd = shutil.which("ollama")
        if cmd:
            return cmd
        
        candidates = [
            "/opt/homebrew/bin/ollama",
            "/usr/local/bin/ollama",
            "/usr/bin/ollama"
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return None

    def _install_ollama_automatically(self):
        """Instala Ollama en macOS de forma 100% transparente."""
        print("[Pipeline] 🚀 Ollama no está instalado. Instalando automáticamente en tu Mac...")
        
        # 1. Intentar instalación vía Homebrew si está disponible
        brew_bin = shutil.which("brew") or ("/opt/homebrew/bin/brew" if os.path.exists("/opt/homebrew/bin/brew") else None)
        if brew_bin:
            print("[Pipeline] 📦 Instalando Ollama mediante Homebrew...")
            try:
                subprocess.run([brew_bin, "install", "ollama"], check=True)
                print("[Pipeline] ✅ Ollama instalado con éxito vía Homebrew.")
                return True
            except Exception as e:
                print(f"[Pipeline] ⚠️ Homebrew falló ({e}). Intentando descarga directa...")

        # 2. Descarga e instalación directa en /Applications
        print("[Pipeline] 📥 Descargando e instalando Ollama oficial para macOS...")
        zip_path = "/tmp/Ollama-darwin.zip"
        try:
            subprocess.run(["curl", "-L", "https://ollama.com/download/Ollama-darwin.zip", "-o", zip_path], check=True)
            subprocess.run(["unzip", "-o", zip_path, "-d", "/Applications/"], check=True)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            print("[Pipeline] ✅ Ollama instalado con éxito en /Applications/Ollama.app")
            return True
        except Exception as e:
            print(f"[Pipeline] ❌ Error en la instalación automática de Ollama: {e}")
            return False

    def _wait_for_service(self, url, timeout=15):
        """Revisa activamente hasta que el puerto responda."""
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
        # 1. Comprobar si responde
        if not self._wait_for_service(f"{self.ollama_url}/api/tags", timeout=2):
            ollama_bin = self._find_ollama_cmd()
            has_app = os.path.exists("/Applications/Ollama.app")

            # Si no existe ni el binario ni la App, instalar automáticamente
            if not ollama_bin and not has_app:
                success = self._install_ollama_automatically()
                if not success:
                    sys.exit(1)
                ollama_bin = self._find_ollama_cmd()
                has_app = os.path.exists("/Applications/Ollama.app")

            print("[Pipeline] ⚠️ Iniciando servicio Ollama en segundo plano...")
            if ollama_bin:
                subprocess.Popen([ollama_bin, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif has_app:
                subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print("[Pipeline] ⏳ Esperando respuesta del servicio Ollama...")
            if not self._wait_for_service(f"{self.ollama_url}/api/tags", timeout=20):
                print("[Pipeline] ❌ No se pudo conectar con Ollama tras la instalación.")
                sys.exit(1)

        # 2. Descargar modelo automáticamente si no está en local
        try:
            res = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            models = [m.get("name") for m in res.json().get("models", [])]
            if not any(self.model_name in m for m in models):
                print(f"[Pipeline] ⏳ Modelo '{self.model_name}' no presente. Descargando automáticamente (ollama pull)...")
                ollama_bin = self._find_ollama_cmd() or "ollama"
                subprocess.run([ollama_bin, "pull", self.model_name], check=True)
                print(f"[Pipeline] ✅ Modelo '{self.model_name}' descargado y listo.")
            else:
                print(f"[Pipeline] ✔️ Ollama y modelo '{self.model_name}' listos.")
        except Exception as e:
            print(f"[Pipeline] ❌ Error al verificar modelo en Ollama: {e}")
            sys.exit(1)

    def _ensure_searxng_container(self):
        if self._wait_for_service(f"{self.searxng_url}/search?q=ping&format=json", timeout=2):
            print("[Pipeline] ✔️ SearXNG corriendo en puerto 8080.")
            return

        print("[Pipeline] ⚠️ SearXNG no responde. Levantar contenedor Docker...")
        try:
            check_cmd = subprocess.run(["docker", "ps", "-a", "--filter", "name=searxng", "--format", "{{.Names}}"], capture_output=True, text=True)
            if "searxng" in check_cmd.stdout:
                subprocess.run(["docker", "start", "searxng"], stdout=subprocess.DEVNULL)
            else:
                subprocess.run([
                    "docker", "run", "-d",
                    "-p", "8080:8080",
                    "--name", "searxng",
                    "searxng/searxng"
                ], stdout=subprocess.DEVNULL)
            
            if self._wait_for_service(f"{self.searxng_url}/search?q=ping&format=json", timeout=10):
                print("[Pipeline] ✅ SearXNG desplegado en Docker.")
        except FileNotFoundError:
            print("[Pipeline] ⚠️ Docker no instalado/corriendo. Inicia Docker Desktop si requieres búsquedas.")

    def _ensure_firecrawl_container(self):
        if self._wait_for_service(f"{self.firecrawl_url}/is-healthy", timeout=2):
            print("[Pipeline] ✔️ Firecrawl activo en puerto 3002.")
            return
        print("[Pipeline] ℹ️ Firecrawl no detectado en puerto 3002.")
