# src/localsumm/transcription.py

import subprocess
import tempfile
import threading
import time
from pathlib import Path

from .config import (
    DOWNLOAD_DIR,
    FASTER_WHISPER_COMPUTE_TYPE,
    FASTER_WHISPER_DEVICE,
    TRANSCRIPTION_BACKEND,
    WHISPER_CPP_EXECUTABLE_PATH,
    WHISPER_CPP_LANGUAGE,
    WHISPER_CPP_MODEL_PATH,
    WHISPER_CPP_THREADS,
    WHISPER_MODEL_SIZE,
)
from .exceptions import (
    ConfigurationError,
    FileProcessingError,
    TranscriptionError,
)

try:
    from .utils import _convert_audio_to_wav_mono16k
except ImportError as e:
    raise ImportError(
        f"Impossible d'importer la fonction de conversion depuis '.utils': {e}"
    ) from e

if TRANSCRIPTION_BACKEND == "faster-whisper":
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print(
            "AVERTISSEMENT: Backend 'faster-whisper' sélectionné mais la bibliothèque n'est pas installée (`pip install faster-whisper ctranslate2`)."
        )
# from loguru import logger

# --- Backend Faster-Whisper ---

_faster_whisper_model = None
_faster_whisper_model_lock = threading.Lock()


def _load_faster_whisper_model() -> "WhisperModel":
    """Charge et retourne le modèle Faster-Whisper (thread-safe)."""
    global _faster_whisper_model
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        # logger.error("La bibliothèque 'faster-whisper' est requise pour utiliser ce backend mais n'est pas installée.")
        raise ConfigurationError(
            "Bibliothèque 'faster-whisper' non installée. Installez-la avec 'pip install faster-whisper ctranslate2'"
        ) from e

    if _faster_whisper_model is None:
        with _faster_whisper_model_lock:
            if _faster_whisper_model is None:
                model_name = WHISPER_MODEL_SIZE
                # logger.info(f"Chargement du modèle Faster-Whisper: {model_name} (Device: {FASTER_WHISPER_DEVICE}, Compute: {FASTER_WHISPER_COMPUTE_TYPE})")
                try:
                    _faster_whisper_model = WhisperModel(
                        model_name,
                        device=FASTER_WHISPER_DEVICE,
                        compute_type=FASTER_WHISPER_COMPUTE_TYPE,
                    )
                    # logger.success(f"Modèle Faster-Whisper '{model_name}' chargé.")
                except Exception as e:
                    # logger.error(f"Échec du chargement du modèle Faster-Whisper: {e}")
                    raise TranscriptionError(
                        f"Impossible de charger le modèle Faster-Whisper '{model_name}': {e}"
                    ) from e
    return _faster_whisper_model


def _transcribe_with_faster_whisper(audio_path: Path) -> str:
    """Effectue la transcription en utilisant le backend Faster-Whisper."""
    model = _load_faster_whisper_model()
    # logger.info(f"Début transcription (Faster-Whisper) pour: {audio_path.name}")
    start_time = time.time()
    try:
        segments, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            language=WHISPER_CPP_LANGUAGE if WHISPER_CPP_LANGUAGE != "auto" else None,
        )
        # logger.info(f"Langue détectée (faster-whisper): {info.language} ({info.language_probability:.2f})")
        transcribed_text: str = "".join(segment.text for segment in segments).strip()
        duration = time.time() - start_time
        # logger.success(f"Transcription Faster-Whisper réussie en {duration:.2f}s.")
        return transcribed_text
    except Exception as e:
        # logger.opt(exception=True).error(f"Transcription Faster-Whisper échouée pour {audio_path.name}.")
        raise TranscriptionError(f"Transcription Faster-Whisper échouée: {e}") from e


# --- Backend Whisper.cpp ---


def _check_whisper_cpp_paths() -> tuple[str, str]:
    """Vérifie si les chemins whisper.cpp sont configurés et existent."""
    exec_path_str = WHISPER_CPP_EXECUTABLE_PATH
    model_path_str = WHISPER_CPP_MODEL_PATH

    # 1. Vérifier si les variables ont été définies (dans .env ou l'environnement)
    if not exec_path_str:
        raise ConfigurationError(
            "Le chemin vers l'exécutable whisper.cpp (WHISPER_CPP_EXECUTABLE_PATH) "
            "n'est pas configuré dans votre fichier .env ou vos variables d'environnement."
        )
    if not model_path_str:
        raise ConfigurationError(
            "Le chemin vers le modèle whisper.cpp (WHISPER_CPP_MODEL_PATH) "
            "n'est pas configuré dans votre fichier .env ou vos variables d'environnement."
        )

    # 2. Convertir en Path et vérifier l'existence du fichier
    exec_path = Path(exec_path_str)
    model_path = Path(model_path_str)

    if not exec_path.is_file():
        raise ConfigurationError(
            f"L'exécutable whisper.cpp est introuvable au chemin configuré : {exec_path}"
        )
    if not model_path.is_file():
        raise ConfigurationError(
            f"Le modèle whisper.cpp est introuvable au chemin configuré : {model_path}"
        )

    return str(exec_path), str(model_path)


def _transcribe_with_whisper_cpp(audio_path: Path) -> str:
    """
    Effectue la transcription via whisper.cpp après avoir CONVERTI l'entrée en WAV 16kHz Mono.
    """
    exec_path, model_path = _check_whisper_cpp_paths()
    # logger.info(f"Préparation pour transcription (whisper.cpp) de: {audio_path.name}")

    with tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False, dir=str(DOWNLOAD_DIR)
    ) as tmp_wav_file:
        temp_wav_path = Path(tmp_wav_file.name)

    # logger.debug(f"Chemin WAV temporaire généré: {temp_wav_path}")

    converted_audio_path_for_whisper: Path = Path("")
    start_time = time.time()

    try:
        # Étape 1: Convertir l'audio d'entrée en WAV 16kHz Mono temporaire
        _convert_audio_to_wav_mono16k(audio_path, temp_wav_path)
        converted_audio_path_for_whisper = (
            temp_wav_path  # Utiliser ce chemin pour whisper.cpp
        )

        # Étape 2: Construire et exécuter la commande whisper.cpp sur le fichier WAV converti
        # logger.info(f"Lancement de whisper.cpp sur le fichier converti: {converted_audio_path_for_whisper.name}")
        command: list[str] = [
            exec_path,
            "-m",
            model_path,
            "-f",
            str(converted_audio_path_for_whisper),  # Utiliser le fichier WAV converti !
            "-l",
            WHISPER_CPP_LANGUAGE,
            "-otxt",
            "-nt",
            "-t",
            WHISPER_CPP_THREADS,
        ]
        # logger.debug(f"Exécution whisper.cpp: {' '.join(shlex.quote(arg) for arg in command)}")

        result: subprocess.CompletedProcess = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding="utf-8"
        )
        duration = time.time() - start_time
        transcribed_text = result.stdout.strip()
        # logger.success(f"Transcription whisper.cpp (via WAV converti) réussie en {duration:.2f}s.")
        # logger.debug(f"Sortie stderr whisper.cpp: {result.stderr.strip()}")
        return transcribed_text

    except FileProcessingError as e:  # Erreur venant de la conversion ffmpeg
        # logger.error(f"Erreur lors de la conversion audio préalable pour whisper.cpp: {e}")
        raise TranscriptionError(
            f"Échec de la préparation audio pour whisper.cpp: {e}"
        ) from e
    except subprocess.CalledProcessError as e:  # Erreur venant de whisper.cpp lui-même
        # logger.error(f"whisper.cpp a échoué (code {e.returncode}). Stderr: {e.stderr.strip()}")
        raise TranscriptionError(
            f"whisper.cpp a échoué (code {e.returncode}): {e.stderr.strip()}"
        ) from e
    except Exception as e:
        # logger.opt(exception=True).error(f"Erreur inattendue lors de la transcription via whisper.cpp.")
        raise TranscriptionError(
            f"Erreur inattendue lors de la transcription via whisper.cpp : {e}"
        ) from e

    finally:
        if converted_audio_path_for_whisper.exists():
            try:
                converted_audio_path_for_whisper.unlink()
                # logger.debug(f"Fichier WAV temporaire '{converted_audio_path_for_whisper.name}' supprimé.")
            except OSError:
                # logger.warning(f"Impossible de supprimer le fichier WAV temporaire {converted_audio_path_for_whisper}: {e}")
                pass


# --- Fonction Principale (Dispatcher) ---


def transcribe_audio(audio_path: Path) -> str:
    """
    Transcrire un fichier audio en utilisant le backend configuré ('faster-whisper' ou 'whisper-cpp').

    Args:
        audio_path: Chemin vers le fichier audio (objet Path).

    Returns:
        Le texte transcrit.

    Raises:
        ConfigurationError: Si le backend configuré est invalide ou mal configuré.
        TranscriptionError: Si la transcription échoue.
        FileNotFoundError: Si le fichier audio n'existe pas.
    """
    if not audio_path.is_file():
        raise FileNotFoundError(
            f"Le fichier audio spécifié n'a pas été trouvé : {audio_path}"
        )

    # logger.info(f"Backend de transcription sélectionné: {TRANSCRIPTION_BACKEND}")

    if TRANSCRIPTION_BACKEND == "faster-whisper":
        return _transcribe_with_faster_whisper(audio_path)
    elif TRANSCRIPTION_BACKEND == "whisper-cpp":
        return _transcribe_with_whisper_cpp(audio_path)
    else:
        # logger.error(f"Backend de transcription non valide configuré: {TRANSCRIPTION_BACKEND}")
        raise ConfigurationError(
            f"Backend de transcription non valide : '{TRANSCRIPTION_BACKEND}'. "
            f"Choisissez 'faster-whisper' ou 'whisper-cpp' dans la configuration."
        )
