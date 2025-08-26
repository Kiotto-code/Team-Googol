import os
import numpy as np
from flask import Blueprint, request, jsonify, send_file
from clip_utils import get_text_embedding, image_data, UPLOAD_FOLDER

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search_image():
    data = request.get_json()
    if 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data['query']

    # Move tensor to CPU and convert to NumPy
    query_emb = get_text_embedding(query).detach().cpu().numpy().flatten()

    results = []

    for fname, item in image_data.items():
        img_emb = np.array(item["image_embedding"], dtype=np.float32)  # list -> numpy array
        # normalize embeddings if you want cosine similarity
        img_score = float(np.dot(query_emb, img_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(img_emb)))

        desc_score = 0.0
        if item.get("description_embedding") is not None:
            desc_emb = np.array(item["description_embedding"], dtype=np.float32)
            desc_score = float(np.dot(query_emb, desc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb)))

        # Combine both scores (average if description available)
        final_score = (img_score + desc_score) / 2 if desc_score != 0 else img_score
        
        # final_score = (0.4 * img_score) + (0.6 * desc_score)


        if final_score > 0.4:
            results.append({
            "filename": fname,
            "description": item.get("description", ""),
            "score": final_score
        })
        
        if not results:
            return jsonify({"message": "Image not found"}), 400

    # Sort by similarity descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    for r in results:
        r["url"] = f"http://127.0.0.1:5000/uploads/{r['filename']}"

    return jsonify({"results": results})
