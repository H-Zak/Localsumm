# src/localsumm/config.py

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Charger les variables d'environnement (.env)
load_dotenv()

# --- Configuration Ollama ---
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Défaut : mistral, surchargeable via .env
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
OLLAMA_API_GENERATE_URL: str = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TIMEOUT: int = 300

# --- Configuration Chemins ---
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Configuration Whisper (Général et Backends) ---

# Choix du backend ('faster-whisper' ou 'whisper-cpp'), défaut 'whisper-cpp'
TRANSCRIPTION_BACKEND: str = os.getenv("TRANSCRIPTION_BACKEND", "whisper-cpp")

# -- Config pour 'faster-whisper' (utilisé si TRANSCRIPTION_BACKEND='faster-whisper') --
# 'medium' pour une bonne transcription, surchargeable via .env
WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "medium")
FASTER_WHISPER_COMPUTE_TYPE: str = os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "int8")
FASTER_WHISPER_DEVICE: str = os.getenv(
    "FASTER_WHISPER_DEVICE", "auto"
)  # Tente MPS/CUDA puis CPU

# -- Config pour 'whisper-cpp' (utilisé si TRANSCRIPTION_BACKEND='whisper-cpp') --
# Lire depuis l'env SANS valeur par défaut de chemin -> doit être dans .env si utilisé
WHISPER_CPP_EXECUTABLE_PATH: Optional[str] = os.getenv("WHISPER_CPP_EXECUTABLE_PATH")
WHISPER_CPP_MODEL_PATH: Optional[str] = os.getenv("WHISPER_CPP_MODEL_PATH")
WHISPER_CPP_LANGUAGE: str = os.getenv("WHISPER_CPP_LANGUAGE", "auto")
WHISPER_CPP_THREADS: str = os.getenv("WHISPER_CPP_THREADS", "4")

# --- Configuration Chunking (Textes Longs) ---
LLM_MAX_CONTEXT_TOKENS: int = 8192  # Fenêtre Llama3/Mistral standard
# Taille cible des chunks en tokens, laissant marge pour prompt/réponse (~75%)
CHUNK_TARGET_TOKENS: int = int(
    os.getenv("CHUNK_TARGET_TOKENS", str(int(LLM_MAX_CONTEXT_TOKENS * 0.75)))
)
# Chevauchement des tokens entre chunks
CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))


# --- Configuration Prompts LLM ---
PROMPT_TEMPLATE_SHORT: str = """
SYSTEM: Tu es un assistant expert en résumé de texte concis et pertinent. Résume le texte suivant en 2 ou 3 phrases maximum, en FRANÇAIS. Capture l'idée principale de manière percutante.
USER: Voici le texte :
{text}
ASSISTANT:"""

PROMPT_TEMPLATE_DETAILED: str = """
SYSTEM: Tu es un assistant expert en synthèse d'information. Extrais les 5 à 7 points clés les plus importants du texte suivant. Présente-les sous forme de liste à puces (commençant par '- ' ou '* '), en FRANÇAIS. Chaque point doit être clair et informatif.
USER: Voici le texte :
{text}
ASSISTANT:"""

# Prompt pour l'étape "Map" du Map-Reduce
PROMPT_TEMPLATE_MAP: str = os.getenv(
    "PROMPT_TEMPLATE_MAP",
    """Résume CONCISEMENT le morceau de texte suivant en FRANÇAIS, en extrayant uniquement les informations et points clés essentiels. Ne fais pas d'introduction ou de conclusion, juste les faits clés du morceau. TEXTE DU MORCEAU : \n\n{text}\n\nRÉSUMÉ CONCIS DES POINTS CLÉS DU MORCEAU :""",
)

# --- Configuration Logging ---
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Path = BASE_DIR / "localsumm.log"

# --- Configuration Tokenizer ---
# Identifiant Hugging Face Hub pour le tokenizer. Doit correspondre au LLM utilisé.
# Voir https://huggingface.co/models pour trouver les identifiants.
# Exemples: "mistralai/Mistral-7B-Instruct-v0.2", "meta-llama/Llama-3-8B-Instruct"
TOKENIZER_HF_IDENTIFIER: str = os.getenv(
    "TOKENIZER_HF_IDENTIFIER", "mistralai/Mistral-7B-Instruct-v0.2"
)
# Verifier que le model HuggingFace correspond a celui de OLLAMA
