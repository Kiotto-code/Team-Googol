from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

# Device
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load BLIP model & processor once
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

def generate_caption(image_path: str, prompt: str = None, max_tokens: int = 100) -> str:
    raw_image = Image.open(image_path).convert("RGB")
    # if prompt:
    #     inputs = processor(images=raw_image, text=prompt, return_tensors="pt").to(device)
    # else:
    #     inputs = processor(images=raw_image, return_tensors="pt").to(device)
        
    custom_prompt = "Describe the item with color, type, material, and unique features:"
    inputs = processor(images=raw_image ,return_tensors="pt").to(device)

    out = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
    )
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption