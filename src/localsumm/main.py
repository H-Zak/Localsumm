# src/localsumm/main.py

import time
from pathlib import Path
from typing import Optional

from .config import (
    CHUNK_OVERLAP_TOKENS,
    CHUNK_TARGET_TOKENS,
    PROMPT_TEMPLATE_DETAILED,
    PROMPT_TEMPLATE_MAP,
    PROMPT_TEMPLATE_SHORT,
)
from .exceptions import (
    ConfigurationError,
    LocalSummError,
    OllamaError,
)
from .file_processor import process_file
from .llm_interaction import generate_summary_with_ollama
from .transcription import transcribe_audio
from .utils import chunk_text, count_tokens
from .youtube_processor import download_youtube_audio

# from loguru import logger

# --- Helper pour Map-Reduce ---


def _summarize_map_reduce(chunks: list[str], final_prompt_template: str) -> str:
    """
    Effectue la partie Map-Reduce de la summarisation pour les textes longs.

    Args:
        chunks: Liste des morceaux de texte.
        final_prompt_template: Le template de prompt final (court ou détaillé).

    Returns:
        Le résumé final combiné.

    Raises:
        OllamaError: Si une erreur survient lors de l'appel à Ollama.
        ConfigurationError: Si le tokenizer ou Ollama est mal configuré.
    """
    # logger.info(f"Démarrage Map-Reduce sur {len(chunks)} chunks.")
    intermediate_summaries: list[str] = []

    # Étape MAP : Résumer chaque chunk individuellement
    # logger.info("--- Étape MAP ---")
    for i, chunk in enumerate(chunks):
        # logger.info(f"Résumé du chunk {i+1}/{len(chunks)}...")
        try:
            chunk_summary: str = generate_summary_with_ollama(
                chunk, PROMPT_TEMPLATE_MAP
            )
            intermediate_summaries.append(chunk_summary)
            # logger.debug(f"Résumé Chunk {i+1}: {chunk_summary[:100]}...")
            time.sleep(0.5)
        except (OllamaError, ConfigurationError):
            # logger.warning(f"Échec du résumé pour le chunk {i+1}. Erreur: {e}. On continue...")
            # Décision: soit on lève l'erreur, soit on continue sans ce chunk.
            # Pour l'instant, on continue, mais on pourrait vouloir arrêter.
            intermediate_summaries.append(f"[Erreur lors du résumé du chunk {i+1}]")
        except Exception as e:
            intermediate_summaries.append(
                f"[Erreur inattendue chunk {i+1}: {type(e).__name__}]"
            )

    # logger.info("--- Fin Étape MAP ---")

    # Étape COMBINE/REDUCE : Combiner les résumés intermédiaires et faire un résumé final
    # logger.info("--- Étape REDUCE ---")
    combined_intermediate_summary: str = "\n\n".join(intermediate_summaries).strip()

    if not combined_intermediate_summary:
        # logger.error("Aucun résumé intermédiaire n'a pu être généré.")
        raise LocalSummError("Aucun résumé intermédiaire généré pendant le Map-Reduce.")

    # Vérifier si les résumés combinés sont eux-mêmes trop longs
    # logger.info("Vérification de la taille des résumés combinés...")
    combined_tokens: int = count_tokens(combined_intermediate_summary)
    # logger.debug(f"Nombre de tokens des résumés intermédiaires combinés: {combined_tokens}")

    # logger.info("Génération du résumé final (Reduce) à partir des résumés intermédiaires...")
    final_summary: str = generate_summary_with_ollama(
        combined_intermediate_summary, final_prompt_template
    )

    # logger.success("Fin Étape REDUCE.")
    return final_summary


# --- Fonction Principale (Mise à jour) ---


def process_input(
    *,
    text_input: Optional[str] = None,
    file_input: Optional[Path] = None,
    url_input: Optional[str] = None,
    detailed: bool = False,
) -> str:
    """
    Fonction principale orchestrant le traitement et gérant les textes longs.
    (Docstring précédent reste valide)
    """
    input_sources = sum(p is not None for p in [text_input, file_input, url_input])
    if input_sources != 1:
        raise ValueError(
            "Erreur interne: La fonction process_input doit recevoir exactement une source d'entrée."
        )

    text_to_summarize: str = ""
    source_description: str = ""
    downloaded_file_path: Optional[Path] = None

    # --- Étape 1: Obtenir le Texte Source (reste identique) ---
    # logger.info("Étape 1: Récupération du texte source...")
    try:
        if text_input:
            source_description = "texte direct"
            text_to_summarize = text_input
        elif url_input:
            source_description = f"URL YouTube: {url_input}"
            downloaded_file_path = download_youtube_audio(url_input)
            text_to_summarize = transcribe_audio(downloaded_file_path)
        elif file_input:
            source_description = f"fichier local: {file_input.name}"
            text_to_summarize = process_file(file_input)
    except (ValueError, LocalSummError) as e:
        raise e
    except Exception as e:
        raise LocalSummError(
            f"Erreur inattendue lors du traitement de l'entrée {source_description}: {e}"
        ) from e

    # --- Étape 2: Vérifier si on a du Texte (reste identique) ---
    # logger.info("Étape 2: Vérification du texte obtenu...")
    if not text_to_summarize or text_to_summarize.isspace():
        return f"Aucun contenu textuel trouvé ou transcrit depuis '{source_description}'. Impossible de générer un résumé."

    # --- Étape 3: Générer le Résumé (MODIFIÉ pour gérer textes longs) ---
    # logger.info("Étape 3: Génération du résumé via LLM (gestion des textes longs)...")
    try:
        num_tokens: int = count_tokens(text_to_summarize)
        # logger.info(f"Nombre de tokens détectés dans le texte source: {num_tokens}")

        final_prompt_template = (
            PROMPT_TEMPLATE_DETAILED if detailed else PROMPT_TEMPLATE_SHORT
        )

        if num_tokens <= CHUNK_TARGET_TOKENS:
            # logger.info("Le texte est assez court. Génération directe du résumé.")
            summary = generate_summary_with_ollama(
                text_to_summarize, final_prompt_template
            )
        else:
            # logger.info(f"Le texte est trop long ({num_tokens} tokens > {CHUNK_TARGET_TOKENS}). Utilisation de Map-Reduce.")
            chunks = chunk_text(
                text_to_summarize, CHUNK_TARGET_TOKENS, CHUNK_OVERLAP_TOKENS
            )

            summary = _summarize_map_reduce(chunks, final_prompt_template)
        # summary = generate_summary_with_ollama(text_to_summarize, final_prompt_template)

        # logger.success("Résumé final généré.")
        return summary

    except (
        OllamaError,
        ConfigurationError,
        ValueError,
        LocalSummError,
    ) as e:  # ValueError peut venir de chunk_text
        # logger.error(f"Erreur lors de la génération du résumé: {e}")
        raise e
    except Exception as e:
        # logger.opt(exception=True).error("Erreur inattendue lors de la génération du résumé.")
        raise LocalSummError(
            f"Erreur inattendue lors de la génération du résumé: {e}"
        ) from e
