# app/services/firestore_user_service.py

import time
from async_lru import alru_cache
from app.db.firestore_client import async_db as db  # ✅ Correct async client

_cached_profiles = {}
CACHE_TTL_SECONDS = 600  # 10 minutes

@alru_cache(maxsize=128)
async def get_user_profile(user_id: str):
    current_time = time.time()
    cache_entry = _cached_profiles.get(user_id)

    if cache_entry and current_time - cache_entry["timestamp"] < CACHE_TTL_SECONDS:
        return cache_entry["data"]

    # ✅ Use async client correctly here
    doc_ref = db.collection("users").document(user_id)
    doc = await doc_ref.get()  # This is now valid
    if doc.exists:
        profile_data = doc.to_dict()
        _cached_profiles[user_id] = {
            "data": profile_data,
            "timestamp": current_time
        }
        return profile_data
    return {}

async def invalidate_user_cache(user_id: str):
    _cached_profiles.pop(user_id, None)
    get_user_profile.cache_clear()
