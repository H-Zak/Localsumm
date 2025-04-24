# src/localsumm/exceptions.py


class LocalSummError(Exception):
    """Exception de base pour toutes les erreurs spécifiques à LocalSumm."""

    pass


class OllamaError(LocalSummError):
    """Erreur survenue lors de l'interaction avec l'API Ollama."""

    pass


class TranscriptionError(LocalSummError):
    """Erreur survenue lors de la transcription audio avec Whisper."""

    pass


class YoutubeDownloadError(LocalSummError):
    """Erreur survenue lors du téléchargement depuis YouTube."""

    pass


class FileProcessingError(LocalSummError):
    """Erreur survenue lors du traitement d'un fichier en entrée
    (lecture, extraction audio, type non supporté, etc.)."""

    pass


class ConfigurationError(LocalSummError):
    """Erreur liée à une configuration invalide ou manquante."""

    pass
