import os
import hashlib
import uuid
import mimetypes
from typing import Tuple
from app.core.config import settings
from app.domain.interfaces import IObjectStorage


class LocalDiskStorage(IObjectStorage):
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    async def store(self, file_bytes: bytes, filename: str, content_type: str) -> Tuple[str, str]:
        # Compute SHA-256
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Generate a unique storage key
        _, ext = os.path.splitext(filename)
        storage_key = f"{uuid.uuid4()}{ext.lower()}"
        file_path = os.path.join(self.base_dir, storage_key)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Store content-type in a companion metadata file
        meta_path = f"{file_path}.meta"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(content_type)

        return storage_key, sha256

    async def retrieve(self, storage_key: str) -> Tuple[bytes, str]:
        file_path = os.path.join(self.base_dir, storage_key)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Storage key '{storage_key}' not found on disk.")

        with open(file_path, "rb") as f:
            data = f.read()

        content_type = "application/octet-stream"
        meta_path = f"{file_path}.meta"
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                content_type = f.read().strip()
        else:
            guessed, _ = mimetypes.guess_type(file_path)
            if guessed:
                content_type = guessed

        return data, content_type

    async def delete(self, storage_key: str) -> None:
        file_path = os.path.join(self.base_dir, storage_key)
        if os.path.exists(file_path):
            os.remove(file_path)
        meta_path = f"{file_path}.meta"
        if os.path.exists(meta_path):
            os.remove(meta_path)

