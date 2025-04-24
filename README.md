# LocalSumm

LocalSumm est un outil local en ligne de commande (CLI) pour générer des résumés structurés (courts ou détaillés) en français. Il peut traiter du texte brut, des fichiers audio/vidéo locaux, ou l'audio d'URLs YouTube en utilisant des modèles d'IA open source (Whisper pour la transcription, Llama 3 / Mistral pour le résumé via Ollama).

## Fonctionnalités

* Résumé de texte fourni directement (`--text`).
* Transcription automatique et résumé de fichiers audio/vidéo locaux (`--file`).
    * Supporte les formats audio/vidéo courants grâce à `ffmpeg`.
    * Utilise Whisper pour la transcription avec un choix de backends :
        * `faster-whisper` (rapide, bonne intégration Python, défaut).
        * `whisper.cpp` (très performant, nécessite configuration manuelle).
    * Backend configurable via le fichier `.env`.
* Téléchargement automatique, transcription et résumé de l'audio de vidéos YouTube (`--url`).
* Génération de résumés courts (par défaut) ou détaillés (`--detailed`).
* Utilisation de Large Language Models (LLM) locaux via **Ollama** (supporte Llama 3, Mistral, etc.).
* Gestion automatique des textes longs (dépassant la fenêtre de contexte du LLM) via découpage (chunking) et résumé itératif (Map-Reduce).
* Configuration simplifiée des paramètres locaux et spécifiques via un fichier `.env`.
* Sortie des résumés en français (configurable via les prompts dans `config.py`).

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les éléments suivants :

1.  **Python :** Version 3.9 ou supérieure.
2.  **Git :** Pour cloner le dépôt. ([https://git-scm.com/](https://git-scm.com/))
3.  **ffmpeg :** Essentiel pour le décodage audio/vidéo par Whisper et l'extraction depuis les vidéos.
    * Sur macOS : `brew install ffmpeg`
    * Sur Debian/Ubuntu : `sudo apt update && sudo apt install ffmpeg`
    * Sur Windows : Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html), extrayez et ajoutez le dossier `bin` à votre PATH système.
4.  **Ollama :** Doit être installé ET **lancé en arrière-plan** pour que le résumé fonctionne.
    * Téléchargez et installez depuis : [https://ollama.com/](https://ollama.com/)
    * Vérifiez qu'il tourne (icône barre de menu sur Mac/Windows, ou `ollama list` dans le terminal).
5.  **Compte Hugging Face :** Nécessaire pour télécharger certains tokenizers (comme celui de Mistral). Créez un compte sur [https://huggingface.co/](https://huggingface.co/).
6.  **(Optionnel, si backend `whisper.cpp` choisi) :**
    * Une version compilée de [whisper.cpp](https://github.com/ggerganov/whisper.cpp) sur votre machine.
    * Un modèle Whisper au format GGUF (ex: `ggml-medium.bin`) téléchargé manuellement.
    * Les outils de compilation C++ (Xcode Command Line Tools sur Mac, `build-essential` sur Linux...).

## Installation

1.  **Cloner le dépôt (remplacez avec votre URL) :**
    ```bash
    git clone [https://github.com/H-Zak/LocalSumm.git](https://github.com/H-Zak/LocalSumm.git)
    cd LocalSumm
    ```
2.  **Créer et activer un environnement virtuel :**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # ou : .\.venv\Scripts\activate  # Windows CMD
    # ou : .\.venv\Scripts\Activate.ps1 # Windows PowerShell
    ```
3.  **Installer les dépendances (y compris les outils de dev) :**
    ```bash
    # Utiliser les guillemets si votre shell (comme zsh) pose problème avec les crochets
    pip install -e '.[dev]'
    ```
4.  **(Optionnel mais recommandé) Installer les hooks pre-commit :**
    ```bash
    pre-commit install
    ```
5.  **Installer le CLI Hugging Face (pour l'authentification) :**
    ```bash
    pip install huggingface_hub
    ```

## Configuration Initiale

### 1. Authentification Hugging Face (Important pour certains modèles)

Certains modèles/tokenizers sur Hugging Face nécessitent d'accepter leurs termes et d'être authentifié pour les télécharger.

1.  **Accepter les Termes sur le Site :**
    * Allez sur la page du modèle dont vous avez besoin (par exemple, pour le tokenizer Mistral par défaut : [https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2)).
    * Connectez-vous avec votre compte Hugging Face.
    * Lisez et acceptez les conditions d'utilisation si demandé. Faites de même pour d'autres modèles "gated" que vous voudriez utiliser (ex: Llama 3).
2.  **Se Connecter Localement via le Terminal :**
    * Générez un Token d'Accès sur Hugging Face : Allez dans `Settings` > `Access Tokens` ([https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)), cliquez sur "New token", donnez-lui un nom (ex: `localsumm-access`), choisissez le rôle `read`, et générez le token. **Copiez ce token immédiatement, il ne sera plus affiché.**
    * Dans votre terminal (avec l'environnement virtuel activé), lancez :
        ```bash
        huggingface-cli login
        ```
    * Collez votre token lorsque demandé et validez.

### 2. Configuration des Modèles LLM (Ollama)

* Lancez l'application Ollama.
* Téléchargez au moins un modèle LLM que vous souhaitez utiliser :
    ```bash
    # Recommandé (bonnes performances en français) :
    ollama pull mistral:7b-instruct
    # Alternative (très performant) :
    # ollama pull llama3:instruct
    ```
* Vérifiez les modèles installés : `ollama list`.

### 3. Configuration Locale (`.env`)

Cette application utilise un fichier `.env` pour les configurations spécifiques à votre machine.

1.  **Copiez le fichier d'exemple :**
    ```bash
    cp .env.example .env
    ```
2.  **IMPORTANT :** Assurez-vous que `.env` est bien listé dans `.gitignore` (il l'est normalement).
3.  **Modifiez le fichier `.env`** avec votre éditeur :
    * **`OLLAMA_MODEL` :** Décommentez et changez si vous voulez utiliser un autre modèle que celui par défaut (ex: `llama3:instruct`).
    * **`TOKENIZER_HF_IDENTIFIER` :** Décommentez et changez **seulement** si vous utilisez un `OLLAMA_MODEL` dont le tokenizer ne correspond pas au défaut (ex: si vous mettez `OLLAMA_MODEL=llama3:instruct`, mettez `TOKENIZER_HF_IDENTIFIER=meta-llama/Llama-3-8B-Instruct`).
    * **`WHISPER_MODEL_SIZE` :** Changez si vous voulez tester un autre modèle Whisper (ex: `medium`). `small` est un bon début.
    * **`TRANSCRIPTION_BACKEND` :** Choisissez `"faster-whisper"` (défaut) ou `"whisper-cpp"`.
    * **Si `TRANSCRIPTION_BACKEND='whisper-cpp'` :**
        * Vous **DEVEZ** décommenter et remplir `WHISPER_CPP_EXECUTABLE_PATH` avec le chemin **absolu** vers votre exécutable `whisper-cli` (ou `main`).
        * Vous **DEVEZ** décommenter et remplir `WHISPER_CPP_MODEL_PATH` avec le chemin **absolu** vers votre fichier modèle `.bin` (gguf) téléchargé.
        * Ajustez `WHISPER_CPP_LANGUAGE` et `WHISPER_CPP_THREADS` si besoin.

## Utilisation (CLI)

Assurez-vous que votre environnement virtuel est activé (`source .venv/bin/activate` ou équivalent) et qu'Ollama est lancé.

* **Afficher l'aide et les options :**
    ```bash
    localsumm --help
    ```
* **Résumer du texte direct :**
    ```bash
    localsumm --text "L'intelligence artificielle évolue rapidement, posant des défis éthiques."
    ```
* **Résumer un fichier (audio, vidéo, ou texte) :**
    ```bash
    # Résumé court par défaut
    localsumm --file chemin/vers/votre/fichier.mp4
    # Résumé détaillé avec -d
    localsumm --file chemin/vers/audio.mp3 -d
    ```
* **Résumer une URL YouTube :**
    ```bash
    localsumm --url "URL_YOUTUBE_VALIDE"
    ```

## Dépannage

* **Erreur `ffmpeg: command not found` :** `ffmpeg` n'est pas installé ou pas dans le PATH. Voir Prérequis.
* **Erreur `OllamaError: Failed to connect...` :** Ollama n'est pas lancé. Démarrez l'application Ollama. Vérifiez `OLLAMA_BASE_URL` dans `.env` si modifié.
* **Erreur `ollama pull ... file does not exist` :** Problème réseau/registre Ollama. Vérifiez connexion, essayez `ollama pull mistral`, mettez à jour Ollama.
* **Erreur `ConfigurationError: Impossible de charger le tokenizer... Access to model... is restricted...` :** Problème d'accès au modèle/tokenizer sur Hugging Face. Voir section "Authentification Hugging Face" (accepter termes + `huggingface-cli login`).
* **Erreur `ConfigurationError: Chemin ... manquant ou invalide dans .env` (pour whisper.cpp) :** Vous avez choisi le backend `whisper-cpp` mais les chemins `WHISPER_CPP_...` sont incorrects ou non définis dans `.env`. Vérifiez les chemins absolus.
* **Erreur `TOML parse error` (au commit) :** Erreur de syntaxe dans `pyproject.toml`. Vérifiez la ligne indiquée.
* **Transcription/Résumé Lent :** Normal pour les fichiers longs ou gros modèles sur CPU. Essayez un modèle Whisper plus petit (`WHISPER_MODEL_SIZE` dans `.env`). `faster-whisper` (défaut) est optimisé. Pour `whisper.cpp`, ajustez `WHISPER_CPP_THREADS`.
* **Qualité Médiocre :** Essayez un modèle Whisper plus grand. Ajustez les prompts (`PROMPT_...`) dans `config.py`. Assurez-vous d'utiliser un LLM "Instruct". Vérifiez la qualité de l'audio source.

## Licence

MIT License - Voir le fichier `LICENSE` pour plus de détails.

## Contribuer

Les contributions sont les bienvenues ! Veuillez ouvrir une "issue" pour discuter des changements majeurs ou soumettre une "Pull Request" pour les corrections/améliorations mineures.
