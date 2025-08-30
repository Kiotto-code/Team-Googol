import os
import time
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from clip_utils import COLLECTOR_FOLDER
from database import collect_found_item, get_box_status, update_box_status

collect_bp = Blueprint('collect', __name__)

@collect_bp.route('/collect', methods=['POST'])
def collect_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image collected"}), 400

    # Get form data
    imgtaken_timestamp = request.form.get('timestamp', "")
    box_id = request.form.get('box_id', "")
    collector_img = request.files['image']
    
    # Generate secure filename
    filename = secure_filename(collector_img.filename)
    if not filename:
        filename = f"collected_{int(time.time())}.jpg"
    
    filepath = os.path.join(COLLECTOR_FOLDER, filename)
    collector_img.save(filepath)
    
    request_received_timestamp = time.time()

    # Convert timestamp to float for comparison
    try:
        img_timestamp = float(imgtaken_timestamp) if imgtaken_timestamp else request_received_timestamp
    except ValueError:
        img_timestamp = request_received_timestamp

    if request_received_timestamp - img_timestamp > 10:
        return jsonify({"error": "Timestamp Exceeded 5 seconds"}), 400
	
    try:
        # Save to database
        item_id = collect_found_item(filename, img_timestamp, box_id)
        
        # Update box load if box_id is provided
        if box_id:
            box_info = get_box_status(box_id)
            if box_info:
                new_load = box_info['current_load'] + 1
                update_box_status(box_id, current_load=new_load)
                
                # If box is full, request collection
                if new_load >= box_info['capacity']:
                    update_box_status(box_id, status='collect_request')
        
        return jsonify({
            "message": "Image collected successfully",
            "filename": filename,
            "item_id": item_id,
            "box_id": box_id,
            "timestamp": img_timestamp
        }), 200
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Failed to save item: {str(e)}"}), 500