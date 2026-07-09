import os
import tempfile

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def transcribe(audio_url):

    response = requests.get(audio_url, timeout=30)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
        f.write(response.content)
        temp_path = f.name

    with open(temp_path, "rb") as audio:

        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            files={
                "file": audio
            },
            data={
                "model": "whisper-large-v3"
            },
            timeout=120,
        )

    os.remove(temp_path)

    response.raise_for_status()

    return response.json()["text"]