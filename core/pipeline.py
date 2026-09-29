import subprocess
import time
import requests
import sys
import os

class SystemPipelineManager:
    def __init__(self):
        self.searxng_url = "http://localhost:8080"
        self.ollama_url = "http://localhost:11434"

    def ensure_ollama(self):
        """Verifica que Ollama esté corriendo y lo inicia silenciosamente si es necesario."""
        try:
            requests.get(self.ollama_url, timeout=2)
            print("[Pipeline] ✔️ Ollama ya está operativo.")
            return
        except requests.ConnectionError:
            pass

        print("[Pipeline] ⚙️ Iniciando servicio Ollama en segundo plano...")
        try:
            # Intento 1: Iniciar vía CLI silencioso
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # Intento 2: Iniciar la aplicación nativa de macOS
            result = subprocess.run(["open", "-a", "Ollama"], capture_output=True, text=True)
            if result.returncode != 0:
                print("\n[Pipeline] ❌ ERROR CRÍTICO: No se encontró Ollama instalado en tu sistema.")
                print("El agente requiere que instales Ollama para continuar.")
                sys.exit(1)

        for _ in range(15):
            time.sleep(2)
            try:
                requests.get(self.ollama_url, timeout=2)
                print("[Pipeline] ✔️ Ollama iniciado correctamente.")
                return
            except requests.ConnectionError:
                pass
        print("[Pipeline] ⚠️ Tiempo de espera agotado al conectar con Ollama.")

    def ensure_docker(self):
        """Verifica que el daemon de Docker esté activo y lo inicia si no lo está."""
        try:
            subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[Pipeline] ⚙️ Iniciando Docker Desktop...")
            subprocess.run(["open", "-a", "Docker"])
            for _ in range(30):
                time.sleep(2)
                try:
                    subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("[Pipeline] ✔️ Docker daemon listo.")
                    return
                except Exception:
                    pass
            print("[Pipeline] ⚠️ No se pudo conectar a Docker Desktop.")

    def ensure_searxng(self):
        """Despliega o reinicia el contenedor de SearXNG."""
        self.ensure_docker()
        try:
            res = requests.get(f"{self.searxng_url}/healthz", timeout=2)
            if res.status_code == 200:
                print("[Pipeline] ✔️ SearXNG ya está operativo en puerto 8080.")
                return
        except Exception:
            pass

        print("[Pipeline] ⚙️ Desplegando contenedor SearXNG...")
        subprocess.run(["docker", "rm", "-f", "searxng"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        cmd = [
            "docker", "run", "-d",
            "-p", "8080:8080",
            "-v", f"{os.getcwd()}/searxng/settings.yml:/etc/searxng/settings.yml",
            "--name", "searxng",
            "searxng/searxng"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("[Pipeline] ✔️ SearXNG iniciado correctamente.")
        else:
            print(f"[Pipeline] ⚠️ Error iniciando SearXNG: {result.stderr.strip()}")

    def ensure_all_services(self):
        print("\n[Pipeline] 🔍 Verificando infraestructura local...")
        self.ensure_ollama()
        self.ensure_searxng()
        print("[Pipeline] ✅ Verificación finalizada.\n")