"""
Docstring for app.main.utils
"""

import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

def save_profile_picture(file_storage) -> str:
    # file_storage = request.files["profile_picture"]
    filename = secure_filename(file_storage.filename)
    if "." not in filename:
        raise ValueError("Bad filename")

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Unsupported file type")

    new_name = f"{secrets.token_hex(16)}.{ext}"
    folder = current_app.config["UPLOAD_PROFILE_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, new_name)
    file_storage.save(path)

    # store only filename in DB
    return new_name
