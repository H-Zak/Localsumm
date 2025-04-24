# src/localsumm/utils.py

import subprocess

# from loguru import logger # Si vous utilisez loguru
import threading
from pathlib import Path
from typing import Optional

from .config import TOKENIZER_HF_IDENTIFIER
from .exceptions import FileProcessingError

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from transformers import AutoTokenizer, PreTrainedTokenizerBase
except ImportError as e:
    print(
        f"ERREUR: Bibliothèques manquantes ({e}). Veuillez installer les dépendances avec:"
    )
    print("pip install -e '.[dev]'")
    print(
        "Assurez-vous que 'transformers', 'tiktoken', 'langchain-text-splitters' sont dans pyproject.toml"
    )
    raise


from .exceptions import ConfigurationError

# from loguru import logger

# --- Gestion du Tokenizer (Singleton Thread-Safe) ---
_tokenizer: Optional[PreTrainedTokenizerBase] = None
_tokenizer_lock = threading.Lock()
_tokenizer_model_name: Optional[str] = None


def get_tokenizer() -> PreTrainedTokenizerBase:
    """
    Charge et retourne le tokenizer correspondant à l'ID Hugging Face configuré (thread-safe).
    Utilise l'identifiant défini dans config.TOKENIZER_HF_IDENTIFIER.
    """
    global _tokenizer, _tokenizer_model_name
    current_hf_id = TOKENIZER_HF_IDENTIFIER
    if not current_hf_id:
        raise ConfigurationError(
            "L'identifiant Hugging Face du Tokenizer (TOKENIZER_HF_IDENTIFIER) n'est pas configuré."
        )

    if _tokenizer is None or _tokenizer_model_name != current_hf_id:
        with _tokenizer_lock:
            if _tokenizer is None or _tokenizer_model_name != current_hf_id:
                # logger.info(f"Chargement du tokenizer pour le modèle : {current_hf_id}...")
                try:
                    # Utiliser trust_remote_code=True peut être nécessaire pour certains modèles, pas pour laama 3 ni pour mistral officiels

                    _tokenizer = AutoTokenizer.from_pretrained(current_hf_id)
                    _tokenizer_model_name = current_hf_id
                    # logger.success(f"Tokenizer pour '{current_hf_id}' chargé.")
                except OSError as e:
                    # logger.error(f"Impossible de télécharger/trouver le tokenizer pour {current_hf_id}. Modèle Ollama mal orthographié ou non disponible sur Hugging Face Hub ? Erreur: {e}")
                    raise ConfigurationError(
                        f"Impossible de charger le tokenizer pour '{current_hf_id}'. "
                        f"Vérifiez le nom du modèle dans OLLAMA_MODEL et sa disponibilité sur Hugging Face Hub. Erreur: {e}"
                    ) from e
                except Exception as e:
                    # logger.opt(exception=True).error(f"Erreur inattendue lors du chargement du tokenizer pour {current_hf_id}.")
                    raise ConfigurationError(
                        f"Erreur inattendue lors du chargement du tokenizer: {e}"
                    ) from e

    if _tokenizer is None:
        raise ConfigurationError("Le tokenizer n'a pas pu être initialisé.")

    return _tokenizer


# --- Fonction de Comptage de Tokens ---
def count_tokens(text: str) -> int:
    """Compte le nombre de tokens dans un texte avec le tokenizer approprié."""
    if not text:
        return 0
    try:
        tokenizer = get_tokenizer()
        return len(tokenizer.encode(text))
    except ConfigurationError as e:
        # logger.error(f"Impossible de compter les tokens car le tokenizer n'a pas pu être chargé: {e}")
        raise e
    except Exception as e:
        # logger.opt(exception=True).error(f"Erreur inattendue lors du comptage des tokens.")
        raise RuntimeError(f"Erreur inattendue lors du comptage des tokens: {e}") from e


# --- Fonction de Découpage (Chunking) ---
def chunk_text(text: str, max_chunk_tokens: int, overlap_tokens: int) -> list[str]:
    """
    Découpe un texte en morceaux (chunks) basés sur un nombre maximum de tokens,
    en utilisant le tokenizer approprié et en gérant le chevauchement.

    Args:
        text: Le texte à découper.
        max_chunk_tokens: Le nombre maximum de tokens par chunk.
        overlap_tokens: Le nombre de tokens de chevauchement entre les chunks.

    Returns:
        Une liste de chaînes de caractères (les chunks).

    Raises:
        ConfigurationError: Si le tokenizer ne peut pas être chargé.
        ValueError: Si les paramètres de chunking sont invalides.
    """
    if max_chunk_tokens <= overlap_tokens:
        raise ValueError("max_chunk_tokens doit être supérieur à overlap_tokens")
    if not text:
        return []

    # logger.info(f"Découpage du texte (longueur: {len(text)}) en chunks de ~{max_chunk_tokens} tokens avec {overlap_tokens} tokens de chevauchement.")

    try:
        tokenizer = get_tokenizer()
    except ConfigurationError as e:
        # logger.error(f"Impossible de découper le texte car le tokenizer n'a pas pu être chargé: {e}")
        raise e

    text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer=tokenizer,
        chunk_size=max_chunk_tokens,
        chunk_overlap=overlap_tokens,
        # length_function=len # Par défaut, utilise la longueur des tokens via le tokenizer fourni
    )

    chunks = text_splitter.split_text(text)
    # logger.success(f"Texte découpé en {len(chunks)} chunks.")
    return chunks


def _convert_audio_to_wav_mono16k(input_path: Path, output_wav_path: Path) -> None:
    """
    Convertit un fichier audio en WAV, 16kHz, 16-bit PCM, Mono en utilisant ffmpeg.
    (C'est la fonction qui était DANS file_processor.py avant)

    Args:
        input_path: Chemin du fichier audio d'entrée.
        output_wav_path: Chemin où sauvegarder le fichier WAV de sortie.

    Raises:
        FileProcessingError: Si ffmpeg échoue.
        FileNotFoundError: Si le fichier d'entrée n'existe pas.
    """
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Fichier audio d'entrée pour conversion introuvable: {input_path}"
        )

    # logger.info(f"Conversion (utils) de '{input_path.name}' en WAV vers '{output_wav_path.name}'...")
    command = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(output_wav_path),
    ]
    # logger.debug(f"Exécution ffmpeg (conversion utils): {' '.join(shlex.quote(arg) for arg in command)}")

    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        # logger.success(f"Conversion en WAV (utils) réussie.")
    except FileNotFoundError:
        # logger.error("La commande 'ffmpeg' est introuvable...")
        raise FileProcessingError(
            "ffmpeg n'est pas installé ou n'est pas dans le PATH système."
        ) from None
    except subprocess.CalledProcessError as e:
        # logger.error(f"ffmpeg a échoué (code {e.returncode}) lors de la conversion en WAV...")
        raise FileProcessingError(
            f"ffmpeg a échoué lors de la conversion en WAV de {input_path.name}: {e.stderr}"
        ) from e
    except Exception as e:
        # logger.opt(exception=True).error("Erreur inattendue lors de la conversion audio WAV via ffmpeg (utils).")
        raise FileProcessingError(
            f"Erreur inattendue lors de la conversion en WAV: {e}"
        ) from e
