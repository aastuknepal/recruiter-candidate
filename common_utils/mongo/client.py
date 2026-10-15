# =============================================================================
# common_utils/mongo/client.py
#
# Singleton PyMongo client.
# Reads MONGO_URI / MONGO_DB_NAME from Django settings.
#
# Usage:
#   from common_utils.mongo.client import get_db
#   db = get_db()
#   db["activity_logs"].insert_one({...})
# =============================================================================
import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from django.conf import settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Return (or create) the singleton MongoClient."""
    global _client
    if _client is None:
        uri = getattr(settings, "MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=3000,   # fail fast if Mongo is down
            connectTimeoutMS=3000,
        )
        logger.debug("MongoClient created: %s", uri)
    return _client


def get_db() -> Database:
    """Return the application's MongoDB database."""
    db_name = getattr(settings, "MONGO_DB_NAME", "apply_logs")
    return get_client()[db_name]
