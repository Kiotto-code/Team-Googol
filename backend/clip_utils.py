import os
import torch
import clip
from PIL import Image
import json

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14@336px", device=device)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_image_embedding(image_path):
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model.encode_image(image)
    return emb / emb.norm(dim=-1, keepdim=True)

def get_text_embedding(text):
    text_tokens = clip.tokenize([text]).to(device)
    with torch.no_grad():
        emb = model.encode_text(text_tokens)
    return emb / emb.norm(dim=-1, keepdim=True)
