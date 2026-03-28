"""Translation service for RSS content."""

import logging
from typing import Optional, Dict, Any, List
from firefeed_core.exceptions import ServiceUnavailableException, ValidationException
from firefeed_core.api_client.client import APIClient
from utils.retry import retry_on_network_error


logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating RSS content."""
    
    def __init__(self, api_client=None):
        """
        Initialize translation service.
        
        Args:
            api_client: Translation API client (optional)
        """
        self.api_client = api_client
        self.supported_languages = ['en', 'ru', 'de', 'fr', 'es', 'it', 'pt']
    
    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def translate_text(
        self, 
        text: str, 
        target_language: str, 
        source_language: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)
            
        Returns:
            Translated text or None if translation fails
        """
        if not text or not isinstance(text, str):
            return None
        
        if target_language not in self.supported_languages:
            logger.warning(f"Unsupported target language: {target_language}")
            return None
        
        # In a real implementation, this would call a translation API
        # For now, return the original text
        logger.info(f"Translation would be performed for text to {target_language}")
        return text
    
    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def translate_rss_item(
        self, 
        item: Dict[str, Any], 
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Translate RSS item fields.
        
        Args:
            item: RSS item dictionary
            target_language: Target language code
            
        Returns:
            Translated item or None if translation fails
        """
        if not item or not isinstance(item, dict):
            return None
        
        translated_item = item.copy()
        
        # Translate title
        if "title" in item:
            translated_title = await self.translate_text(
                item["title"], 
                target_language
            )
            if translated_title:
                translated_item["title"] = translated_title
        
        # Translate description
        if "description" in item:
            translated_description = await self.translate_text(
                item["description"], 
                target_language
            )
            if translated_description:
                translated_item["description"] = translated_description
        
        # Translate content
        if "content" in item:
            translated_content = await self.translate_text(
                item["content"], 
                target_language
            )
            if translated_content:
                translated_item["content"] = translated_content
        
        # Add translation metadata
        translated_item["translated"] = True
        translated_item["target_language"] = target_language
        
        return translated_item
    
    async def translate_multiple_items(
        self, 
        items: List[Dict[str, Any]], 
        target_language: str
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Translate multiple RSS items.
        
        Args:
            items: List of RSS items
            target_language: Target language code
            
        Returns:
            List of translated items
        """
        import asyncio
        
        if not items:
            return []
        
        tasks = [
            self.translate_rss_item(item, target_language) 
            for item in items
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        translated_items = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to translate item {i}: {result}")
                translated_items.append(None)
            else:
                translated_items.append(result)
        
        return translated_items
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.supported_languages.copy()
    
    async def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code or None
        """
        if not text:
            return None
        
        # In a real implementation, this would call a language detection API
        # For now, return None
        logger.info("Language detection would be performed")
        return None