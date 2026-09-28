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
        """Busca el ejecutable de Docker en las rutas comunes de macOS."""
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

    def _install_docker_automatically(self):
        """Instala Docker Desktop en macOS automáticamente."""
        print("[Pipeline] 🚀 Docker no está instalado. Instalando automáticamente en tu Mac...")
        brew_bin = shutil.which("brew") or ("/opt/homebrew/bin/brew" if os.path.exists("/opt/homebrew/bin/brew") else None)
        if brew_bin:
            print("[Pipeline] 📦 Instalando Docker Desktop mediante Homebrew...")
            try:
                subprocess.run([brew_bin, "install", "--cask", "docker"], check=True)
                print("[Pipeline] ✅ Docker Desktop instalado vía Homebrew.")
                return True
            except Exception as e:
                print(f"[Pipeline] ⚠️ Homebrew falló ({e}). Intentando descarga directa...")

        dmg_path = "/tmp/Docker.dmg"
        mount_point = "/Volumes/Docker"
        try:
            print("[Pipeline] 📥 Descargando Docker Desktop para Apple Silicon...")
            url = "https://desktop.docker.com/mac/main/arm64/Docker.dmg"
            subprocess.run(["curl", "-L", url, "-o", dmg_path], check=True)
            print("[Pipeline] 📦 Instalando Docker.app en /Applications...")
            subprocess.run(["hdiutil", "attach", dmg_path], check=True)
            subprocess.run(["cp", "-R", f"{mount_point}/Docker.app", "/Applications/"], check=True)
            subprocess.run(["hdiutil", "detach", mount_point], check=True)
            if os.path.exists(dmg_path):
                os.remove(dmg_path)
            print("[Pipeline] ✅ Docker Desktop instalado con éxito en /Applications/Docker.app")
            return True
        except Exception as e:
            print(f"[Pipeline] ❌ Error en la instalación automática de Docker: {e}")
            return False

    def _ensure_docker_daemon(self):
        """Garantiza la disponibilidad del ejecutable y servicio Docker."""
        docker_bin = self._find_docker_cmd()
        has_app = os.path.exists("/Applications/Docker.app")

        if not docker_bin and not has_app:
            if not self._install_docker_automatically():
                return False
            docker_bin = self._find_docker_cmd()
            has_app = os.path.exists("/Applications/Docker.app")

        docker_cmd = docker_bin or "docker"

        # Verificar si el daemon ya está respondiendo
        try:
            res = subprocess.run([docker_cmd, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return True
        except FileNotFoundError:
            pass

        print("[Pipeline] ⚠️ Docker Desktop no está en ejecución. Iniciándolo automáticamente...")
        if has_app:
            subprocess.run(["open", "-a", "Docker"])

        print("[Pipeline] ⏳ Esperando respuesta del servicio Docker...")
        start_time = time.time()
        while time.time() - start_time < 45:
            if not docker_bin:
                docker_bin = self._find_docker_cmd()
                docker_cmd = docker_bin or "docker"
            try:
                res = subprocess.run([docker_cmd, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    print("[Pipeline] ✅ Daemon de Docker activo.")
                    return True
            except FileNotFoundError:
                pass
            time.sleep(3)
        return False

    def _ensure_searxng_container(self):
        if self._wait_for_service(f"{self.searxng_url}/search?q=ping&format=json", timeout=2):
            print("[Pipeline] ✔️ SearXNG corriendo en puerto 8080.")
            return

        if not self._ensure_docker_daemon():
            print("[Pipeline] ⚠️ No se pudo inicializar Docker. Las búsquedas locales se omitirán temporalmente.")
            return

        docker_bin = self._find_docker_cmd() or "docker"

        print("[Pipeline] 🚀 Desplegando contenedor SearXNG en Docker...")
        try:
            check_cmd = subprocess.run([docker_bin, "ps", "-a", "--filter", "name=searxng", "--format", "{{.Names}}"], capture_output=True, text=True)
            if "searxng" in check_cmd.stdout:
                subprocess.run([docker_bin, "start", "searxng"], stdout=subprocess.DEVNULL)
            else:
                subprocess.run([
                    docker_bin, "run", "-d",
                    "-p", "8080:8080",
                    "--name", "searxng",
                    "searxng/searxng"
                ], stdout=subprocess.DEVNULL)
            
            if self._wait_for_service(f"{self.searxng_url}/search?q=ping&format=json", timeout=15):
                print("[Pipeline] ✅ SearXNG desplegado en Docker.")
            else:
                print("[Pipeline] ⚠️ SearXNG tardó en responder en el puerto 8080.")
        except Exception as e:
            print(f"[Pipeline] ⚠️ Error al desplegar SearXNG: {e}")

    def _ensure_firecrawl_container(self):
        if self._wait_for_service(f"{self.firecrawl_url}/is-healthy", timeout=2):
            print("[Pipeline] ✔️ Firecrawl activo en puerto 3002.")
            return
        print("[Pipeline] ℹ️ Firecrawl no detectado en puerto 3002 (Opcional).")
