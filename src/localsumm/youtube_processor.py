# src/localsumm/youtube_processor.py

import uuid
from pathlib import Path
from typing import Any, Optional

import yt_dlp  # Bibliothèque pour télécharger depuis YouTube

from .config import DOWNLOAD_DIR
from .exceptions import YoutubeDownloadError

# from loguru import logger # Décommentez si vous utilisez Loguru


def download_youtube_audio(url: str) -> Path:
    """
    Télécharge la meilleure piste audio d'une URL YouTube dans le dossier configuré.

    Args:
        url: L'URL de la vidéo YouTube.

    Returns:
        L'objet Path vers le fichier audio téléchargé (ex: .mp3, .m4a, .opus).

    Raises:
        YoutubeDownloadError: Si le téléchargement échoue.
    """
    # logger.info(f"Tentative de téléchargement audio depuis l'URL YouTube : {url}")

    unique_id = uuid.uuid4()
    output_filename_template = f"youtube_{unique_id}.%(ext)s"
    output_path_template = DOWNLOAD_DIR / output_filename_template

    ydl_opts: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": str(output_path_template),
        # Ne pas télécharger la playlist entière si l'URL est une playlist
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "128",  # Qualité audio (pour codecs lossy)
            }
        ],
        "quiet": True,
        "noprogress": True,
    }

    final_path: Optional[Path] = None

    try:
        # logger.debug(f"Options yt-dlp : {ydl_opts}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            potential_files = list(DOWNLOAD_DIR.glob(f"youtube_{unique_id}*"))

            if not potential_files:
                # logger.error(f"Aucun fichier audio trouvé après téléchargement pour l'ID {unique_id}")
                raise YoutubeDownloadError(
                    f"Impossible de trouver le fichier audio téléchargé pour l'URL {url}"
                )
            final_path = potential_files[0]
            # logger.success(f"Audio téléchargé et extrait avec succès vers : {final_path}")
            return final_path

    except yt_dlp.utils.DownloadError as e:
        # logger.error(f"Erreur de téléchargement yt-dlp pour {url}: {e}")
        raise YoutubeDownloadError(
            f"Échec du téléchargement audio depuis {url}: {e}"
        ) from e
    except Exception as e:
        # logger.opt(exception=True).error(f"Erreur inattendue pendant le téléchargement YouTube pour {url}.")
        raise YoutubeDownloadError(
            f"Erreur inattendue pendant le téléchargement depuis {url}: {e}"
        ) from e
    finally:
        # Ce bloc 'finally' est juste un exemple, le nettoyage pourrait être fait ailleurs.
        # Dans certains workflows, on pourrait vouloir supprimer le fichier téléchargé
        # APRES la transcription et le résumé, pas ici.
        # if final_path and final_path.exists():
        #     logger.debug(f"Nettoyage (exemple) : suppression de {final_path}")
        #     # final_path.unlink() # Attention: Ne pas décommenter si on veut garder le fichier !
        pass
