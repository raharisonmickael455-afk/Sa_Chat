import os
from dotenv import load_dotenv

load_dotenv()

class AIServiceError(Exception):
    """Expected errors returned by the AI provider."""


SYSTEM_INSTRUCTION = (
    "Tu es Sacha AI, l'assistant officiel du reseau social Sa Chat. "
    "Reponds dans la langue de l'utilisateur (francais, malgache ou anglais). "
    "Sois naturel, professionnel, pedagogique et concis. "
    "Tu peux aider a utiliser Sa Chat, expliquer, resumer, traduire, generer du texte "
    "et corriger du code. N'invente pas d'informations et ne pretends jamais avoir "
    "effectue une action. Tu n'as acces a aucune donnee privee ni a aucun outil."
)
MODEL_NAME = "gemini-2.5-flash"


def generate_reply(messages):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise AIServiceError("Sacha AI n'est pas configure. Ajoutez GEMINI_API_KEY au serveur.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))
        contents = [
            types.Content(
                role="user" if message.role == "user" else "model",
                parts=[types.Part.from_text(text=message.content)],
            )
            for message in messages
        ]
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
        )
        answer = (response.text or "").strip()
        if not answer:
            raise AIServiceError("Sacha AI n'a pas fourni de reponse.")
        return answer
    except AIServiceError:
        raise
    except Exception as error:
        raise AIServiceError("Le service Sacha AI est temporairement indisponible.") from error