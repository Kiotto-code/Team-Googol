import json
import os
from typing import Any

_DISABLE_CLIP = os.environ.get("DISABLE_CLIP_MODEL", "").lower() in {"1", "true", "yes"}

try:
    if not _DISABLE_CLIP:
        import clip  # type: ignore
        import torch
        from PIL import Image
    else:  # pragma: no cover - exercised when CLIP is explicitly disabled
        clip = None  # type: ignore
        torch = None  # type: ignore
        Image = None  # type: ignore
except Exception:  # pragma: no cover - handles missing optional deps
    clip = None  # type: ignore
    torch = None  # type: ignore
    Image = None  # type: ignore

if clip is not None and torch is not None:
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    _model, _preprocess = clip.load("ViT-L/14@336px", device=_device)
else:  # pragma: no cover - executed when model cannot be loaded
    _device = "cpu"
    _model = None
    _preprocess = None

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
COLLECTOR_FOLDER = os.environ.get("COLLECTOR_FOLDER", "collectors")
os.makedirs(COLLECTOR_FOLDER, exist_ok=True)

DATA_FILE = os.environ.get("CLIP_DATA_FILE", "data.json")
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        image_data: dict[str, Any] = json.load(file)
else:
    image_data = {}


def save_data() -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(image_data, file)


def _ensure_model_loaded() -> None:
    if _model is None or _preprocess is None or clip is None or torch is None or Image is None:
        raise RuntimeError("CLIP model is disabled or unavailable in this environment")


def get_image_embedding(image_path: str):
    _ensure_model_loaded()
    image = _preprocess(Image.open(image_path)).unsqueeze(0).to(_device)
    with torch.no_grad():
        embedding = _model.encode_image(image)
    return embedding / embedding.norm(dim=-1, keepdim=True)


def get_text_embedding(text: str):
    _ensure_model_loaded()
    tokens = clip.tokenize([text]).to(_device)
    with torch.no_grad():
        embedding = _model.encode_text(tokens)
    return embedding / embedding.norm(dim=-1, keepdim=True)
