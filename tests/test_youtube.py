# test_youtube.py

import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from localsumm.config import DOWNLOAD_DIR
    from localsumm.exceptions import YoutubeDownloadError
    from localsumm.youtube_processor import download_youtube_audio
except ImportError as e:
    print(f"Erreur d'importation. Structure src/localsumm/ correcte ? Détail: {e}")
    sys.exit(1)

YOUTUBE_URL_TO_TEST = "https://www.youtube.com/watch?v=CVOXMaM60ug"


print("--- Test du Téléchargement YouTube ---")
print(f"URL Cible : {YOUTUBE_URL_TO_TEST}")
print(f"Dossier de téléchargement configuré : {DOWNLOAD_DIR}")

if YOUTUBE_URL_TO_TEST == "URL_YOUTUBE_A_REMPLACER":
    print(
        "\nERREUR : Veuillez modifier la variable YOUTUBE_URL_TO_TEST dans le script avec une vraie URL YouTube."
    )
    sys.exit(1)

print("\nTentative de téléchargement de l'audio...")
print("(Cela peut prendre un moment selon la vidéo et votre connexion)...")

start_time = time.time()

try:
    downloaded_audio_path = download_youtube_audio(YOUTUBE_URL_TO_TEST)
    end_time = time.time()
    duration = end_time - start_time

    print("\n--- Résultat ---")
    print(f"Téléchargement terminé avec succès en {duration:.2f} secondes.")
    print(f"Fichier audio sauvegardé ici : {downloaded_audio_path}")

    if downloaded_audio_path.exists() and downloaded_audio_path.is_file():
        print("Vérification : Le fichier existe.")
        file_size = downloaded_audio_path.stat().st_size
        print(f"Taille du fichier : {file_size / 1024:.2f} KB")
        if file_size == 0:
            print("ATTENTION : Le fichier téléchargé est vide !")
    else:
        print("ATTENTION : Le chemin retourné n'existe pas ou n'est pas un fichier !")


except YoutubeDownloadError as e:
    print("\n--- Erreur de Téléchargement YouTube ---")
    print("Une erreur spécifique à yt-dlp est survenue :")
    print(e)
    print(
        "Vérifiez l'URL, votre connexion internet, et l'installation de yt-dlp/ffmpeg."
    )
except Exception as e:
    print("\n--- Erreur Inattendue ---")
    print("Une erreur inattendue est survenue :")

    print(f"Type: {type(e).__name__}, Détails: {e}")


print("\n--- Fin du Test ---")
