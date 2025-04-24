# test_interaction.py

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from localsumm.config import OLLAMA_MODEL, PROMPT_TEMPLATE_SHORT
    from localsumm.exceptions import OllamaError
    from localsumm.llm_interaction import generate_summary_with_ollama
except ImportError as e:
    print(
        "Erreur d'importation. Assurez-vous d'avoir bien la structure src/localsumm/..."
    )
    print(f"Détail: {e}")
    sys.exit(1)


test_text = """
L'intelligence artificielle (IA) est un domaine de l'informatique qui vise à créer
des machines capables de simuler l'intelligence humaine. Cela inclut des tâches
comme l'apprentissage, la résolution de problèmes, la perception, la compréhension
du langage naturel et la prise de décision. Les applications de l'IA sont vastes,
allant des assistants virtuels et des voitures autonomes aux diagnostics médicaux
et à la découverte scientifique. Les modèles de langage étendus (LLM), comme GPT,
Llama ou Mistral, sont une sous-catégorie de l'IA qui a montré des capacités
impressionnantes dans la génération et la compréhension de texte. Cependant, le
développement de l'IA soulève également des questions éthiques importantes
concernant la vie privée, la partialité des algorithmes et l'impact sur l'emploi.
"""

print("--- Test de l'Interaction avec Ollama ---")
print(f"Modèle configuré : {OLLAMA_MODEL}")
print(f'Texte à résumer (début) : "{test_text[:100]}..."')
print("\nAppel de la fonction generate_summary_with_ollama...")

try:
    summary = generate_summary_with_ollama(test_text, PROMPT_TEMPLATE_SHORT)

    print("\n--- Résultat ---")
    print("Appel réussi !")
    print("Résumé reçu :")
    print(summary)

except OllamaError as e:
    print("\n--- Erreur ---")
    print("Une erreur spécifique à Ollama est survenue :")
    print(e)
    print(
        "Vérifiez que Ollama est bien lancé et que le modèle spécifié est disponible."
    )
except Exception as e:
    print("\n--- Erreur Inattendue ---")
    print("Une erreur inattendue est survenue :")
    print(e)

print("\n--- Fin du Test ---")
