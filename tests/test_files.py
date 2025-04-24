# test_files.py

import sys
import time
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from localsumm.exceptions import (
        ConfigurationError,
        FileProcessingError,
        LocalSummError,
        TranscriptionError,
    )
    from localsumm.file_processor import process_file
except ImportError as e:
    print(f"Erreur d'importation. Structure src/localsumm/ correcte ? Détail: {e}")
    sys.exit(1)

# --- IMPORTANT : Modifiez ces chemins pour correspondre à VOS fichiers de test ---
PATH_TO_TEXT_FILE = Path("test.wav.txt")
PATH_TO_AUDIO_FILE = Path("test.wav")
PATH_TO_VIDEO_FILE = Path("test.mp4")
# -----------------------------------------------------------------------------


def run_test(file_path: Path) -> Any:
    """Fonction helper pour tester process_file avec un fichier donné."""
    print(f"\n--- Test du Fichier : {file_path.name} ---")
    if not file_path.exists():
        print(
            f"ERREUR : Le fichier de test '{file_path}' n'existe pas. Vérifiez le chemin."
        )
        return

    print("Appel de process_file...")
    start_time = time.time()
    try:
        content = process_file(file_path)
        end_time = time.time()
        duration = end_time - start_time
        print(f"Traitement réussi en {duration:.2f} secondes.")
        print("-" * 20)
        print("Contenu Retourné (début) :")
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 20)

    except FileNotFoundError as e:
        print(f"ERREUR : Fichier non trouvé pendant le traitement : {e}")
    except (
        FileProcessingError,
        TranscriptionError,
        ConfigurationError,
        LocalSummError,
    ) as e:
        print(f"ERREUR pendant le traitement de {file_path.name} :")
        print(f"  Type d'erreur: {type(e).__name__}")
        print(f"  Message: {e}")
    except Exception as e:
        print(f"ERREUR INATTENDUE pendant le traitement de {file_path.name} :")
        print(f"  Type d'erreur: {type(e).__name__}")
        print(f"  Message: {e}")


# --- Exécution des Tests ---
print("=" * 40)
print(" DÉMARRAGE DES TESTS DE FILE_PROCESSOR ")
print("=" * 40)
print(
    "Assurez-vous qu'Ollama tourne si un backend LLM est nécessaire indirectement (pas le cas ici normalement)"
)
print("Assurez-vous que ffmpeg est installé si vous testez une vidéo.")

# Tester le fichier texte
run_test(PATH_TO_TEXT_FILE)

# Tester le fichier audio
run_test(PATH_TO_AUDIO_FILE)

# Tester le fichier vidéo
run_test(PATH_TO_VIDEO_FILE)

print("\n" + "=" * 40)
print(" FIN DES TESTS DE FILE_PROCESSOR ")
print("=" * 40)
