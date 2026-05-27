"""Context storage backends (Supabase, Redis)."""

import os
import json
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class ContextStorage(ABC):
    """Base class for context storage."""
    
    @abstractmethod
    async def save(self, key: str, data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass


class SupabaseContextStorage(ContextStorage):
    """Supabase-backed context storage."""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if url and key:
                self.client = create_client(url, key)
        except Exception as e:
            print(f"Error initializing Supabase client: {e}")
    
    async def save(self, key: str, data: Dict[str, Any]) -> bool:
        if not self.client:
            return False
        try:
            response = self.client.table("context_cache").upsert({
                "cache_key": key,
                "context_data": json.dumps(data)
            }).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error saving context: {e}")
            return False
    
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            response = self.client.table("context_cache").select("*").eq("cache_key", key).execute()
            if response.data:
                return json.loads(response.data[0]["context_data"])
        except Exception as e:
            print(f"Error loading context: {e}")
        return None
    
    async def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            response = self.client.table("context_cache").delete().eq("cache_key", key).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error deleting context: {e}")
            return False


class InMemoryContextStorage(ContextStorage):
    """In-memory context storage (Phase 3 default, for testing)."""
    
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}
    
    async def save(self, key: str, data: Dict[str, Any]) -> bool:
        self.store[key] = data
        return True
    
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        return self.store.get(key)
    
    async def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            return True
        return False
