# src/localsumm/file_processor.py

import mimetypes  # Pour deviner le type de fichier
import subprocess  # Pour appeler ffmpeg
import time
from pathlib import Path
from typing import Optional

from .config import DOWNLOAD_DIR
from .exceptions import FileProcessingError
from .transcription import (
    transcribe_audio,  # Fonction de transcription (qui utilise le backend configuré)
)

# from loguru import logger # Décommentez si vous utilisez Loguru

mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/quicktime", ".mov")
mimetypes.add_type("video/x-matroska", ".mkv")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("audio/x-wav", ".wav")
mimetypes.add_type("audio/ogg", ".ogg")
mimetypes.add_type("audio/opus", ".opus")


def _extract_audio_from_video(video_path: Path, output_audio_path: Path) -> None:
    """
    Extrait la piste audio d'un fichier vidéo en utilisant ffmpeg via subprocess.
    Sauvegarde au format WAV.

    Args:
        video_path: Chemin vers le fichier vidéo.
        output_audio_path: Chemin où sauvegarder le fichier audio extrait (doit finir par .wav).

    Raises:
        FileProcessingError: Si ffmpeg n'est pas trouvé ou échoue.
    """
    # logger.info(f"Tentative d'extraction audio (WAV) de '{video_path.name}' vers '{output_audio_path.name}'...")
    command: list[str] = [
        "ffmpeg",
        "-i",
        str(video_path),  # Input
        "-vn",  # Pas de vidéo
        "-acodec",
        "pcm_s16le",  # Codec standard pour WAV 16 bits
        "-ar",
        "16000",  # Échantillonnage 16kHz (préféré par Whisper)
        "-ac",
        "1",  # Mono (souvent suffisant pour la voix)
        "-y",  # Écraser si existe
        str(output_audio_path),
    ]
    # logger.debug(f"Exécution ffmpeg: {' '.join(shlex.quote(arg) for arg in command)}")

    try:
        result: subprocess.CompletedProcess = subprocess.run(
            command, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        # logger.success(f"Audio extrait avec succès (WAV) via ffmpeg.")
    except FileNotFoundError as e:
        # logger.error("La commande 'ffmpeg' est introuvable...")
        raise FileProcessingError(
            "ffmpeg n'est pas installé ou n'est pas dans le PATH système."
        ) from e
    except subprocess.CalledProcessError as e:
        # logger.error(f"ffmpeg a échoué (code {e.returncode}) lors de l'extraction WAV...")
        raise FileProcessingError(
            f"ffmpeg a échoué lors de l'extraction audio (WAV): {e.stderr}"
        ) from e
    except Exception as e:
        # logger.opt(exception=True).error("Erreur inattendue lors de l'extraction audio WAV via ffmpeg.")
        raise FileProcessingError(
            f"Erreur inattendue lors de l'extraction audio (WAV): {e}"
        ) from e


def process_file(file_path: Path) -> str:
    """
    Traite un fichier local (texte, audio, vidéo) et retourne son contenu textuel.
    Pour l'audio/vidéo, le contenu retourné est le texte transcrit.

    Args:
        file_path: Chemin vers le fichier local.

    Returns:
        Contenu textuel du fichier (lu directement ou transcrit).

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        FileProcessingError: Si le type de fichier n'est pas supporté ou si une erreur survient.
        TranscriptionError: Si la transcription échoue (remontée depuis transcribe_audio).
        ConfigurationError: Si un backend de transcription est mal configuré.
    """
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Le fichier d'entrée spécifié n'a pas été trouvé : {file_path}"
        )

    # logger.info(f"Traitement du fichier local : {file_path.name}")
    mime_type: Optional[str]
    mime_type, _ = mimetypes.guess_type(file_path)
    # logger.debug(f"Type MIME détecté pour '{file_path.name}': {mime_type}")

    if mime_type is None:
        ext: str = file_path.suffix.lower()
        if ext in [
            ".txt",
            ".md",
            ".py",
            ".json",
            ".csv",
            ".toml",
            ".yaml",
            ".log",
        ]:  # Fichiers texte courants
            mime_type = "text/plain"
        elif ext in [
            ".mp3",
            ".wav",
            ".m4a",
            ".ogg",
            ".flac",
            ".opus",
            ".aac",
        ]:  # Fichiers audio courants
            mime_type = "audio/generic"
        elif ext in [
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
        ]:  # Fichiers vidéo courants
            mime_type = "video/generic"

    if mime_type is None:
        # logger.error(f"Impossible de déterminer le type du fichier : {file_path.name}")
        raise FileProcessingError(
            f"Type de fichier inconnu ou non supporté pour {file_path.name}"
        )

    # --- Traitement basé sur le Type MIME ---

    if mime_type.startswith("text/"):
        # logger.info("Fichier texte détecté. Lecture du contenu.")
        try:
            # Lire le fichier texte en UTF-8 (le plus courant)
            text_content: str = file_path.read_text(encoding="utf-8")
            # logger.success(f"Lecture réussie du fichier texte '{file_path.name}'.")
            return text_content
        except Exception as e:
            # logger.error(f"Erreur lors de la lecture du fichier texte {file_path.name}: {e}")
            raise FileProcessingError(
                f"Impossible de lire le fichier texte {file_path.name}: {e}"
            ) from e

    elif mime_type.startswith("audio/"):
        # logger.info("Fichier audio détecté. Lancement de la transcription...")
        return transcribe_audio(file_path)

    elif mime_type.startswith("video/"):
        # logger.info("Fichier vidéo détecté. Extraction de l'audio nécessaire...")
        timestamp: int = int(time.time())
        temp_audio_filename: str = f"extracted_audio_{file_path.stem}_{timestamp}.wav"  # Utiliser opus comme pour yt-dlp
        temp_audio_path: Path = DOWNLOAD_DIR / temp_audio_filename
        # logger.debug(f"Chemin audio temporaire : {temp_audio_path}")

        try:
            # Étape 1: Extraire l'audio
            _extract_audio_from_video(file_path, temp_audio_path)

            # Étape 2: Transcrire l'audio extrait
            # logger.info("Audio extrait. Lancement de la transcription...")
            transcribed_text = transcribe_audio(temp_audio_path)
            # logger.success(f"Transcription réussie pour la vidéo '{file_path.name}'.")
            return transcribed_text

        finally:
            if temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                    # logger.debug(f"Fichier audio temporaire '{temp_audio_path.name}' supprimé.")
                except OSError:
                    # logger.warning(f"Impossible de supprimer le fichier audio temporaire {temp_audio_path}: {e}")
                    pass

    else:
        # logger.warning(f"Type de fichier non supporté '{mime_type}' pour {file_path.name}")
        raise FileProcessingError(
            f"Type de fichier non supporté '{mime_type}' pour le fichier {file_path.name}"
        )
