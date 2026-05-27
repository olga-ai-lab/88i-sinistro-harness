"""Context engine core — injects domain knowledge into prompts."""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ContextProvider(ABC):
    """Base class for context providers."""
    
    @abstractmethod
    async def get_context(self, **kwargs) -> Dict[str, Any]:
        """Get context data for prompt injection."""
        pass


class ContextEngine:
    """Manages context providers and injects domain knowledge into prompts."""
    
    def __init__(self):
        self.providers: Dict[str, ContextProvider] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def register_provider(self, name: str, provider: ContextProvider):
        """Register a context provider."""
        self.providers[name] = provider
        logger.info(f"Registered context provider: {name}")
    
    async def inject_context(
        self,
        prompt: str,
        providers: List[str],
        context_data: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None
    ) -> str:
        """Inject context from registered providers into prompt."""
        try:
            context_data = context_data or {}
            injected_context = []
            
            for provider_name in providers:
                if provider_name not in self.providers:
                    logger.warning(f"Provider {provider_name} not registered")
                    continue
                
                provider = self.providers[provider_name]
                context = await provider.get_context(**context_data)
                
                if context:
                    injected_context.append(context)
            
            # Build final prompt with context
            if injected_context:
                context_str = "\n\n".join([
                    str(c) if isinstance(c, (str, int, float)) else f"```json\n{c}\n```"
                    for c in injected_context
                ])
                final_prompt = f"Context:\n{context_str}\n\nUser Query:\n{prompt}"
            else:
                final_prompt = prompt
            
            return final_prompt
        except Exception as e:
            logger.error(f"Error injecting context: {e}")
            return prompt
    
    async def get_cached_context(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached context."""
        return self.cache.get(cache_key)
    
    async def cache_context(self, cache_key: str, context: Dict[str, Any]):
        """Cache context for future use."""
        self.cache[cache_key] = context
