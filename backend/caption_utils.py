import mimetypes
import os
from typing import Optional

import google.generativeai as genai

_API_KEY = os.environ.get("GEMINI_API_KEY")
_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
_gemini_model: Optional[genai.GenerativeModel]

if _API_KEY:
    try:  # pragma: no cover - network configuration paths
        genai.configure(api_key=_API_KEY)
        _gemini_model = genai.GenerativeModel(_MODEL_NAME)
    except Exception:  # pragma: no cover - gracefully degrade when API unavailable
        _gemini_model = None
else:
    _gemini_model = None


def generate_caption_with_gemini(image_path: str, prompt: Optional[str] = None) -> str:
    """Generate a caption using the Gemini Vision API if credentials are configured."""

    if _gemini_model is None:
        return "Automatic captioning unavailable."

    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as file:
        img_bytes = file.read()

    image_blob = {"mime_type": mime_type, "data": img_bytes}
    query = prompt if prompt else "Describe this image accurately."

    response = _gemini_model.generate_content(
        [query, image_blob],
        generation_config={
            "max_output_tokens": 60,
            "temperature": 0.7,
            "top_p": 0.9,
        },
    )

    return response.text.strip()
