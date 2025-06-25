import time
from typing import Dict, List, Any

class CacheService:
    def __init__(self):
        self.cache_storage: Dict[str, Dict[str, Any]] = {}  # Stores cache_key: {'data': ..., 'expiry': ...}
        self.hits = 0
        self.misses = 0
        self.cleaned_items = 0

    def cache_extraction_results(self, file_path: str, results: Dict, ttl: int = 3600) -> bool:
        """Caches file extraction results."""
        if not file_path or not isinstance(results, dict):
            return False

        cache_key = f"extraction:{file_path}"
        expiry_time = time.time() + ttl
        self.cache_storage[cache_key] = {"data": results, "expiry": expiry_time}
        return True

    def cache_graph_queries(self, query_hash: str, results: List[Dict], ttl: int = 1800) -> bool:
        """Caches graph query results."""
        if not query_hash or not isinstance(results, list):
            return False

        expiry_time = time.time() + ttl
        self.cache_storage[query_hash] = {"data": results, "expiry": expiry_time}
        return True

    def get_cached_results(self, cache_key: str) -> Any:
        """Gets cached results. Returns None if not found or expired."""
        entry = self.cache_storage.get(cache_key)
        if entry and time.time() < entry["expiry"]:
            self.hits += 1
            return entry["data"]
        elif entry: # Expired
            self.misses += 1
            del self.cache_storage[cache_key] # Remove expired entry
            return None
        else: # Not found
            self.misses += 1
            return None

    def invalidate_cache(self, pattern: str = None) -> bool:
        """
        Invalidates cache entries.
        If pattern is None, clears all cache.
        Otherwise, removes keys containing the pattern.
        """
        initial_size = len(self.cache_storage)
        if pattern is None:
            self.cache_storage.clear()
        else:
            keys_to_delete = [key for key in self.cache_storage if pattern in key]
            for key in keys_to_delete:
                del self.cache_storage[key]

        self.cleaned_items += (initial_size - len(self.cache_storage))
        return True

    def get_cache_statistics(self) -> Dict:
        """Returns cache statistics."""
        total_accesses = self.hits + self.misses
        hit_rate = (self.hits / total_accesses) * 100 if total_accesses > 0 else 0

        return {
            "total_items": len(self.cache_storage),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percentage": round(hit_rate, 2),
            "cleaned_items_since_last_call": self.cleaned_items # This might be better as total cleaned if state is persistent
        }

    def _cleanup_expired_entries(self):
        """Internal method to periodically clean up expired entries."""
        # This could be called periodically by a background task or on certain operations
        now = time.time()
        keys_to_delete = [key for key, entry in self.cache_storage.items() if now >= entry["expiry"]]
        for key in keys_to_delete:
            del self.cache_storage[key]
            self.cleaned_items +=1
