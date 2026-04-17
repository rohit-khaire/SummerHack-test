"""
database.py — Data-access layer with MongoDB support and an automatic
in-memory fallback when MongoDB is unavailable.

This ensures the app works out of the box even without MongoDB running.
"""

from datetime import datetime, timezone
import asyncio

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "digital_twin"
COLLECTION_NAME = "vitals"

# Will be set to True if we successfully connect to MongoDB
_use_mongo = False

# Motor references (only populated when MongoDB is available)
_client = None
_collection = None

# In-memory fallback storage
_memory_store: list[dict] = []
_MAX_MEMORY = 200  # keep last 200 records in memory


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
async def connect_db():
    """Try to connect to MongoDB; fall back to in-memory store on failure."""
    global _use_mongo, _client, _collection

    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # Force a connection attempt to see if MongoDB is available
        await client.admin.command("ping")

        _client = client
        _collection = client[DATABASE_NAME][COLLECTION_NAME]
        await _collection.create_index("timestamp", expireAfterSeconds=3600)
        _use_mongo = True
        print("✅ Connected to MongoDB")
    except Exception as e:
        _use_mongo = False
        print(f"⚠️  MongoDB unavailable ({e}). Using in-memory storage.")


async def close_db():
    """Close the MongoDB connection if it was opened."""
    global _client
    if _client:
        _client.close()
        print("🔌 MongoDB connection closed")


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

async def insert_vitals(vitals: dict):
    """Insert a single vitals document with a UTC timestamp."""
    vitals["timestamp"] = datetime.now(timezone.utc).isoformat()

    if _use_mongo:
        await _collection.insert_one(vitals.copy())
    else:
        _memory_store.append(vitals.copy())
        # Keep memory bounded
        if len(_memory_store) > _MAX_MEMORY:
            del _memory_store[: len(_memory_store) - _MAX_MEMORY]


async def get_latest_vitals() -> dict | None:
    """Return the most recent vitals document."""
    if _use_mongo:
        doc = await _collection.find_one(sort=[("timestamp", -1)])
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    else:
        return _memory_store[-1].copy() if _memory_store else None


async def get_vitals_history(n: int = 30) -> list[dict]:
    """Return the last *n* vitals readings, oldest-first (for charting)."""
    if _use_mongo:
        cursor = _collection.find().sort("timestamp", -1).limit(n)
        docs = await cursor.to_list(length=n)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        docs.reverse()
        return docs
    else:
        return [d.copy() for d in _memory_store[-n:]]
