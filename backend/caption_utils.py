import os
import google.generativeai as genai
from PIL import Image
import mimetypes

# Configure Gemini
genai.configure(api_key="AIzaSyD_idahnFwrGVOLRR0BRWllLoktughMdAo")
model = genai.GenerativeModel("gemini-2.5-flash-lite")

def generate_caption_with_gemini(image_path: str, prompt: str = None) -> str:
    """
    Generate a caption using Gemini Vision API.
    """
    # Detect mime type automatically
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # default

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    # Create the proper Gemini image input format
    image_blob = {"mime_type": mime_type, "data": img_bytes}

    query = prompt if prompt else "Describe this image accurately."

    # Send both prompt and image blob	
    # response = model.generate_content([query, image_blob])
    
    response = model.generate_content(
        [query, image_blob],
        generation_config={
            "max_output_tokens": 60,  # limits response length
            "temperature": 0.7,              # controls creativity
            "top_p": 0.9                     # nucleus sampling
        }
    )

    return response.text.strip()
