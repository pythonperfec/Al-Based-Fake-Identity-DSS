from typing import Generator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.domain.interfaces import IObjectStorage, IJobQueue
from app.services.storage import LocalDiskStorage
from app.services.queue import InProcessJobQueue

_storage_instance = LocalDiskStorage()
_queue_instance = InProcessJobQueue()


def get_storage() -> IObjectStorage:
    return _storage_instance


def get_queue() -> IJobQueue:
    return _queue_instance


__all__ = [
    "get_db",
    "get_current_user",
    "require_role",
    "get_storage",
    "get_queue",
]

