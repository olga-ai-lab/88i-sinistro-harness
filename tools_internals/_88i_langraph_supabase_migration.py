"""Migrate langraph state from in-memory to Supabase."""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SupabaseStateStorage:
    """Supabase-backed state storage (replaces Phase 2 in-memory)."""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Supabase client with environment credentials."""
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if url and key:
                self.client = create_client(url, key)
                logger.info("Supabase client initialized successfully")
            else:
                logger.warning("SUPABASE_URL or SUPABASE_KEY not set in environment")
        except ImportError:
            logger.warning("supabase package not installed")
        except Exception as e:
            logger.warning(f"Error initializing Supabase client: {e}")
    
    async def save_state(
        self,
        conversation_id: str,
        sinistro_id: str,
        estado: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """Save conversation state to Supabase.
        
        Args:
            conversation_id: Unique conversation identifier
            sinistro_id: Associated claim/sinistro identifier
            estado: State data to persist
            ttl_hours: Time-to-live in hours (default: 24)
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not self.client:
            logger.debug("Supabase client not available, returning False")
            return False
        
        try:
            cache_key = f"conv_{conversation_id}"
            
            response = self.client.table("context_cache").upsert({
                "cache_key": cache_key,
                "conversation_id": conversation_id,
                "sinistro_id": sinistro_id,
                "context_data": estado,
                "metadata": {
                    "updated_at": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "ttl_hours": ttl_hours
            }).execute()
            
            success = bool(response.data)
            logger.info(f"State saved for conversation {conversation_id}: {success}")
            return success
        except Exception as e:
            logger.error(f"Error saving state to Supabase: {e}")
            return False
    
    async def load_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from Supabase.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Optional[Dict[str, Any]]: State data if found, None otherwise
        """
        if not self.client:
            logger.debug("Supabase client not available, returning None")
            return None
        
        try:
            cache_key = f"conv_{conversation_id}"
            response = self.client.table("context_cache").select("*").eq("cache_key", cache_key).execute()
            
            if response.data:
                state_data = response.data[0]["context_data"]
                logger.info(f"State loaded for conversation {conversation_id}")
                return state_data
            else:
                logger.debug(f"No state found for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error loading state from Supabase: {e}")
        
        return None
    
    async def delete_state(self, conversation_id: str) -> bool:
        """Delete conversation state from Supabase.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            bool: True if delete successful, False otherwise
        """
        if not self.client:
            logger.debug("Supabase client not available, returning False")
            return False
        
        try:
            cache_key = f"conv_{conversation_id}"
            response = self.client.table("context_cache").delete().eq("cache_key", cache_key).execute()
            
            success = bool(response.data)
            logger.info(f"State deleted for conversation {conversation_id}: {success}")
            return success
        except Exception as e:
            logger.error(f"Error deleting state from Supabase: {e}")
            return False


class InMemoryStateStorage:
    """In-memory fallback state storage for testing/development."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.store: Dict[str, Dict[str, Any]] = {}
        logger.info("In-memory state storage initialized")
    
    async def save_state(
        self,
        conversation_id: str,
        sinistro_id: str,
        estado: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """Save state to in-memory storage.
        
        Args:
            conversation_id: Unique conversation identifier
            sinistro_id: Associated claim/sinistro identifier
            estado: State data to persist
            ttl_hours: Time-to-live (stored but not enforced)
            
        Returns:
            bool: Always True for in-memory storage
        """
        cache_key = f"conv_{conversation_id}"
        self.store[cache_key] = {
            "conversation_id": conversation_id,
            "sinistro_id": sinistro_id,
            "context_data": estado,
            "ttl_hours": ttl_hours,
            "created_at": datetime.now().isoformat()
        }
        logger.debug(f"State saved in-memory for conversation {conversation_id}")
        return True
    
    async def load_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load state from in-memory storage.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Optional[Dict[str, Any]]: State data if found, None otherwise
        """
        cache_key = f"conv_{conversation_id}"
        if cache_key in self.store:
            return self.store[cache_key].get("context_data")
        logger.debug(f"No state found in-memory for conversation {conversation_id}")
        return None
    
    async def delete_state(self, conversation_id: str) -> bool:
        """Delete state from in-memory storage.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            bool: True if deleted, False if not found
        """
        cache_key = f"conv_{conversation_id}"
        if cache_key in self.store:
            del self.store[cache_key]
            logger.debug(f"State deleted in-memory for conversation {conversation_id}")
            return True
        return False


def get_state_storage() -> SupabaseStateStorage:
    """Factory function to get appropriate state storage backend.
    
    Returns SupabaseStateStorage if credentials available, otherwise
    returns InMemoryStateStorage for fallback.
    
    Returns:
        Union[SupabaseStateStorage, InMemoryStateStorage]: State storage backend
    """
    storage = SupabaseStateStorage()
    if storage.client:
        return storage
    else:
        logger.info("Falling back to in-memory state storage")
        return InMemoryStateStorage()
