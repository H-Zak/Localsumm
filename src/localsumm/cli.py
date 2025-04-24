# src/localsumm/cli.py

import pathlib
import time
from typing import Annotated, Optional

import typer
from rich.console import Console  # Pour afficher des erreurs formatées

from .exceptions import LocalSummError

# Importer la fonction principale et les exceptions
from .main import process_input

try:
    from . import __version__
except ImportError:
    __version__ = "N/A"

app = typer.Typer(
    help="LocalSumm 🤖 : Génère des résumés locaux de texte, "
    "fichiers audio/vidéo ou URL YouTube.",
    add_completion=False,
    invoke_without_command=True,  # permet à la fonction callback de s'exécuter
)

error_console = Console(stderr=True, style="bold red")
console = Console()


def version_callback(value: bool) -> None:
    if value:
        print(f"LocalSumm Version: {__version__}")
        raise typer.Exit()


# Fonction principale (anciennement la commande 'summarize')
# Elle est maintenant attachée au callback principal de l'application
@app.callback()
def main(
    ctx: typer.Context,  # Contexte Typer, utile pour invoke_without_command
    # --- Options d'entrée ---
    text_input: Annotated[
        Optional[str],
        typer.Option(
            "--text",
            "-t",
            help="Texte direct à résumer (alternative à --file ou --url).",
        ),
    ] = None,
    file_input: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            "--file",
            "-f",
            help="Chemin vers un fichier local (texte, audio, vidéo) à résumer.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    url_input: Annotated[
        Optional[str], typer.Option("--url", "-u", help="URL YouTube à résumer.")
    ] = None,
    # --- Options de sortie ---
    detailed: Annotated[
        bool,
        typer.Option(
            "--detailed",
            "-d",
            help="Génère un résumé détaillé (points clés) au lieu d'un résumé court.",
        ),
    ] = False,
    # --- Option Version (doit être dans le callback principal) ---
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Affiche la version de LocalSumm et quitte.",
        callback=version_callback,
        is_eager=True,
    ),
    # --- Optionnel : Choix du transcriber ---
    # transcriber_backend: Annotated[Optional[str], typer.Option(...) ] = None,
) -> None:
    """
    Point d'entrée principal de LocalSumm CLI.
    Génère un résumé à partir d'une source de texte (direct, fichier, URL).
    """
    # Empêche l'exécution si une sous-commande est appelée (si on en ajoute plus tard)
    # ou si seule l'option --version a été utilisée (géré par is_eager et Exit)
    if ctx.invoked_subcommand is not None:
        return
    # --- Mesure du Temps ---
    start_time: float = time.perf_counter()  # <--- DÉMARRER LE COMPTEUR ICI

    # --- Validation et Logique Principale (déplacée depuis l'ancienne commande 'summarize') ---

    # Vérifier qu'une et une seule source est fournie (sauf si --version a déjà quitté)
    input_sources: int = sum(p is not None for p in [text_input, file_input, url_input])
    if input_sources == 0:
        print(
            "Erreur : Aucune source d'entrée fournie. Utilisez --text, --file, ou --url."
        )
        # Afficher l'aide peut être utile ici
        # print("\n" + ctx.get_help()) # Décommentez pour afficher l'aide complète
        raise typer.Exit(code=1)
    if input_sources > 1:
        print(
            "Erreur : Fournissez une seule source d'entrée (--text, --file, ou --url)."
        )
        raise typer.Exit(code=1)

    console.print("🚀 [bold green]Démarrage de LocalSumm...[/]")
    summary: str = ""
    exit_code: int = 0

    # rich.spinner.Spinner("Traitement en cours..."): # Pour un indicateur visuel

    try:
        with console.status(
            "🔄 Résumé en cours...", spinner="dots", spinner_style="bold green"
        ):
            summary = process_input(
                text_input=text_input,
                file_input=file_input,
                url_input=url_input,
                detailed=detailed,
                # Si on ajoutait le choix du backend :
                # transcriber_backend=transcriber_backend
            )

        console.print("\n" + "=" * 10 + " Résumé " + "=" * 10)
        console.print(summary)
        console.print("=" * 37)
        console.print("✅ Terminé !")

    except LocalSummError as e:
        error_console.print(f"\nErreur de l'application : {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        error_console.print(f"\nErreur inattendue : {type(e).__name__} - {e}")
        raise typer.Exit(code=1) from e
    finally:
        # --- Calcul et Affichage du Temps Total ---

        end_time: float = time.perf_counter()
        total_duration: float = end_time - start_time
        console.print(f"\n⏱️ Temps d'exécution total : {total_duration:.2f} secondes")

        if exit_code != 0:
            raise typer.Exit(code=exit_code)


# Pas besoin de if __name__ == "__main__": app() ici, car c'est géré par le point d'entrée
