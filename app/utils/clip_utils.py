import os
import torch
import clip
from PIL import Image
import numpy as np


device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14@336px", device=device)


UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_image_embedding(image_path: str) -> torch.Tensor:
    """
    Generates a normalized CLIP embedding vector for an image.
    """
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model.encode_image(image)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb

def get_text_embedding(text: str) -> torch.Tensor:
    """
    Generates a normalized CLIP embedding vector for text.
    """
    text_tokens = clip.tokenize([text]).to(device)
    with torch.no_grad():
        emb = model.encode_text(text_tokens)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb


# 5️⃣  Helper: Convert embedding to JSON-safe format
def tensor_to_list(tensor: torch.Tensor) -> list[float]:
    """
    Converts a torch tensor into a list of floats for database storage.
    """
    return tensor.detach().cpu().numpy().flatten().tolist()


# -------------------------------------------------------
# 6️⃣  Example helper for DB storage (optional)
# -------------------------------------------------------
def generate_item_embeddings(image_path: str, text: str) -> dict:
    """
    Convenience function: generates both image and text embeddings
    and returns a dictionary ready to save to your database.
    """
    img_emb = tensor_to_list(get_image_embedding(image_path))
    text_emb = tensor_to_list(get_text_embedding(text))

    return {
        "image_embedding": img_emb,
        "description_embedding": text_emb,
    }
