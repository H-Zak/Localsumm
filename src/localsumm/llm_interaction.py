# src/localsumm/llm_interaction.py

import json
from typing import Any

import requests

from .config import OLLAMA_API_GENERATE_URL, OLLAMA_MODEL
from .exceptions import OllamaError

# from loguru import logger # Décommentez si vous utilisez Loguru pour le logging


def generate_summary_with_ollama(text: str, prompt_template: str) -> str:
    """
    Génère un résumé en utilisant un template de prompt spécifique via l'API Ollama.

    Args:
        text: Le texte à résumer.
        prompt_template: Le template de prompt (chaîne de caractères)
                         contenant la placeholder {text}.

    Returns:
        Le texte du résumé généré.

    Raises:
        OllamaError: Si la requête API échoue ou si Ollama retourne une erreur.
    """

    full_prompt = prompt_template.format(text=text)
    # logger.debug(f"Envoi requête à Ollama. Prompt début: {full_prompt[:150]}...") # Log du début du prompt

    try:
        # Préparer les données à envoyer à l'API Ollama
        payload: dict[str, Any] = {
            "model": OLLAMA_MODEL,  # Utiliser le modèle défini dans config.py
            "prompt": full_prompt,
            "stream": False,  # On veut la réponse complète, pas en streaming
            "options": {  # Quelques options possibles pour l'inférence
                "temperature": 0.5,  # Contrôle le caractère aléatoire (plus bas = plus déterministe)
                # "top_p": 0.9,          # Autre méthode de contrôle (nucleus sampling)
                # "num_predict": 512     # Limite max de tokens à générer si besoin
            },
        }

        # logger.info(f"Appel de l'API Ollama : {OLLAMA_API_GENERATE_URL}")

        response = requests.post(OLLAMA_API_GENERATE_URL, json=payload, timeout=300)
        response.raise_for_status()
        # logger.info(f"Ollama a répondu avec le statut : {response.status_code}")

        response_data: dict[str, Any] = response.json()

        if "error" in response_data:
            # logger.error(f"Ollama a retourné une erreur : {response_data['error']}")
            raise OllamaError(
                f"Ollama a retourné une erreur : {response_data['error']}"
            )

        if "response" not in response_data:
            # logger.error("La réponse d'Ollama ne contient pas la clé 'response'. Réponse reçue : {response_data}")
            raise OllamaError(
                "Réponse invalide reçue d'Ollama (champ 'response' manquant)."
            )

        summary: str = response_data["response"].strip()
        # logger.success("Résumé reçu avec succès d'Ollama.")
        return summary

    # Gérer les erreurs de connexion ou de timeout
    except requests.exceptions.RequestException as e:
        # logger.error(f"Échec de la requête API vers Ollama : {e}")
        raise OllamaError(
            f"Impossible de contacter l'API Ollama à {OLLAMA_API_GENERATE_URL}: {e}"
        ) from e
    # Gérer les erreurs de décodage JSON (si la réponse n'est pas du JSON valide)
    except json.JSONDecodeError as e:
        # logger.error(f"Échec du décodage de la réponse JSON d'Ollama : {e}. Réponse brute: {response.text[:500]}")
        raise OllamaError(f"Réponse JSON invalide reçue d'Ollama : {e}") from e
    # Gérer d'autres erreurs potentielles (ex: raise_for_status)
    except Exception as e:
        # logger.opt(exception=True).error("Erreur inattendue durant l'interaction avec Ollama.")
        raise OllamaError(
            f"Une erreur inattendue est survenue durant l'interaction avec Ollama : {e}"
        ) from e
