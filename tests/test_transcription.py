# test_transcription.py

import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


try:
    from localsumm.config import WHISPER_MODEL_SIZE
    from localsumm.exceptions import TranscriptionError
    from localsumm.transcription import transcribe_audio
except ImportError as e:
    print(f"Erreur d'importation. Structure src/localsumm/ correcte ? Détail: {e}")
    sys.exit(1)

AUDIO_FILE_TO_TEST = Path("extrait.wav")
# -----------------------------------------------------------------------------

print("--- Test de la Transcription Audio ---")
print(f"Fichier audio cible : {AUDIO_FILE_TO_TEST}")
print(f"Modèle Whisper configuré : {WHISPER_MODEL_SIZE}")

if not AUDIO_FILE_TO_TEST.exists():
    print(f"\nERREUR : Le fichier audio '{AUDIO_FILE_TO_TEST}' n'a pas été trouvé.")
    print("Vérifiez le nom et l'emplacement du fichier.")
    sys.exit(1)

print(
    "\nChargement du modèle Whisper (si pas déjà fait) et début de la transcription..."
)
print("(Cela peut prendre du temps, surtout la première fois ou pour un audio long)...")

start_time = time.time()

try:
    transcribed_text = transcribe_audio(AUDIO_FILE_TO_TEST)
    end_time = time.time()
    duration = end_time - start_time

    print("\n--- Résultat ---")
    print(f"Transcription terminée avec succès en {duration:.2f} secondes.")
    print("\nTexte Transcrit :")
    print("-" * 20)
    print(transcribed_text)
    print("-" * 20)

except FileNotFoundError as e:
    print("\n--- Erreur ---")
    print(f"Le fichier audio n'a pas été trouvé : {e}")
except TranscriptionError as e:
    print("\n--- Erreur de Transcription ---")
    print("Une erreur spécifique à la transcription est survenue :")
    print(e)
    print("Vérifiez le format du fichier audio et l'installation de Whisper/ffmpeg.")
except Exception as e:
    print("\n--- Erreur Inattendue ---")
    print("Une erreur inattendue est survenue :")
    print(e)

print("\n--- Fin du Test ---")
