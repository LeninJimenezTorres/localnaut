import sys
import warnings
warnings.filterwarnings("ignore")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from core.pipeline import SystemPipelineManager
from core.session import TaskSession
from agents.orchestrator_agent import LocalNautOrchestrator

console = Console()

def print_help():
    help_text = """
[bold cyan]Comandos de Sesión CLI:[/bold cyan]
  [green]/help[/green]     - Muestra este menú de ayuda
  [green]/clear[/green]    - Limpia la pantalla de la terminal
  [green]/reset[/green]    - Reinicia la memoria de la conversación actual
  [green]/history[/green]  - Muestra el historial de mensajes de la sesión
  [green]/exit[/green]     - Salir de LocalNaut CLI
"""
    console.print(Panel(help_text, title="LocalNaut Help", border_style="cyan"))

def run_repl(orchestrator, session):
    console.print("\n[bold cyan]LocalNaut CLI[/bold cyan] [dim](qwen2.5-coder:14b | SearXNG Local)[/dim]")
    console.print("[dim]Escribe tu consulta o [/dim][green]/help[/green][dim] para ver los comandos disponibles. Usa [/dim][green]/exit[/green][dim] para salir.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]localnaut>[/bold green]").strip()

            if not user_input:
                continue

            if user_input.lower() == "/exit":
                console.print("[yellow]Cerrando sesión de LocalNaut. ¡Hasta luego![/yellow]")
                break
            elif user_input.lower() == "/clear":
                console.clear()
                continue
            elif user_input.lower() == "/reset":
                session.reset()
                console.print("[bold yellow]✓ Memoria de la sesión reiniciada.[/bold yellow]")
                continue
            elif user_input.lower() == "/help":
                print_help()
                continue
            elif user_input.lower() == "/history":
                console.print(f"[bold dim]Mensajes en sesión: {len(session.messages)}[/bold dim]")
                continue

            with console.status("[bold blue]Procesando...", spinner="dots") as status:
                def update_status(msg):
                    status.update(f"[bold blue]{msg}")

                response_text = orchestrator.process_turn(session, user_input, status_callback=update_status)

            console.print("\n" + "─"*60)
            console.print(Markdown(response_text))
            console.print("─"*60)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Sesión interrumpida. Saliendo...[/yellow]")
            break

def main():
    pipeline = SystemPipelineManager()
    pipeline.ensure_all_services()

    orchestrator = LocalNautOrchestrator()
    session = TaskSession()

    if len(sys.argv) > 1:
        # Modo comando único (Single Shot)
        user_query = " ".join(sys.argv[1:])
        with console.status("[bold blue]Ejecutando consulta...", spinner="dots") as status:
            response = orchestrator.process_turn(session, user_query, status_callback=lambda m: status.update(f"[bold blue]{m}"))
        console.print(Markdown(response))
    else:
        # Modo interactivo REPL (Estilo Claude CLI)
        run_repl(orchestrator, session)

if __name__ == "__main__":
    main()
