from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from werkzeug.utils import secure_filename

# Public router (no auth)
router = APIRouter(prefix="", tags=["activity"])  # root-level path

# Directory where activity images will be stored (under app/activity)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTIVITY_DIR = os.path.join(BASE_DIR, "activity")
os.makedirs(ACTIVITY_DIR, exist_ok=True)


def _build_filename(box_id: int, original_name: str) -> str:
    base = secure_filename(os.path.splitext(original_name)[0]) or "upload"
    ext = os.path.splitext(original_name)[1].lower() or ".jpg"
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"box{box_id}_{ts}{ext if ext.startswith('.') else '.' + ext}"


@router.post("/log/activity", status_code=status.HTTP_201_CREATED)
async def log_activity(box_id: int = Form(...), picture: UploadFile | None = None) -> dict[str, Any]:
    """
    Public endpoint to log an activity snapshot.
    - Accepts: box_id (form field), picture (file)
    - Saves under /activity and returns the public path
    """
    if picture is None or not picture.filename:
        raise HTTPException(status_code=400, detail="picture file is required")

    filename = _build_filename(box_id, picture.filename)
    dest_path = os.path.join(ACTIVITY_DIR, filename)

    # Persist file
    try:
        with open(dest_path, "wb") as f:
            f.write(await picture.read())
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    # Build public URL path (served by main.py mount at /activity)
    public_path = f"/activity/{filename}"

    return {
        "message": "activity logged",
        "box_id": box_id,
        "file_path": public_path,
    }
