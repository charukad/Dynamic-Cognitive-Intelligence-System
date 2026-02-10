"""
Translator Agent - Multilingual Translation and Localization

Expert in language translation, localization, and cross-cultural communication.
Supports 100+ languages with context-aware translation.
"""

from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime

from pydantic import BaseModel

from src.services.agents.base_agent import BaseAgent
from src.core import get_logger

logger = get_logger(__name__)


#============================================================================
# Enums and Types
# ============================================================================

class LanguageCode(str, Enum):
    """Common language codes (ISO 639-1)"""
    EN = "en"  # English
    ES = "es"  # Spanish
    FR = "fr"  # French
    DE = "de"  # German
    ZH = "zh"  # Chinese
    JA = "ja"  # Japanese
    KO = "ko"  # Korean
    AR = "ar"  # Arabic
    RU = "ru"  # Russian
    PT = "pt"  # Portuguese
    IT = "it"  # Italian
    NL = "nl"  # Dutch
    HI = "hi"  # Hindi
    TR = "tr"  # Turkish
    PL = "pl"  # Polish


# ============================================================================
# Data Models
#============================================================================

class LanguageDetection(BaseModel):
    """Language detection result"""
    language: str
    language_name: str
    confidence: float
    alternatives: List[Tuple[str, float]] = []


class Translation(BaseModel):
    """Translation result"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float
    alternatives: List[str] = []
    detected_topics: List[str] = []


class LocalizedContent(BaseModel):
    """Localized content with cultural adaptations"""
    content: Dict[str, str]
    locale: str
    applied_rules: List[str]
    date_format: str
    currency_symbol: str
    number_format: str


# ============================================================================
# Translator Agent
# ============================================================================

class TranslatorAgent(BaseAgent):
    """
    Expert in multilingual translation and localization.
    
    Capabilities:
    - Translate between 100+ languages
    - Context-aware translation
    - Language detection
    - Cultural localization
    - Technical terminology handling
    - Batch translation
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specialty = "translation"
        
        # Simulated translation memory cache
        self.translation_cache: Dict[str, Translation] = {}
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt"""
        return """You are an expert Translator Agent with deep knowledge in:

- 100+ languages and dialects
- Cultural nuances and idioms
- Technical terminology across domains
- Localization best practices
- Translation memory systems
- Context preservation

Your role is to:
1. Provide accurate, natural translations
2. Detect language automatically
3. Preserve context and intent
4. Adapt content culturally
5. Handle technical terms appropriately
6. Maintain consistent terminology

Always provide:
- Natural, fluent translations
- Cultural context when relevant
- Alternative translations when appropriate
- Confidence scores for quality assessment
"""
    
    async def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "en",
        context: Optional[str] = None
    ) -> Translation:
        """
        Translate text with context preservation.
        
        Args:
            text: Text to translate
            source_lang: Source language (auto-detect if None)
            target_lang: Target language
            context: Additional context for better translation
            
        Returns:
            Translation result
        """
        # Check cache
        cache_key = f"{text}:{source_lang}:{target_lang}"
        if cache_key in self.translation_cache:
            logger.info("Translation cache hit")
            return self.translation_cache[cache_key]
        
        # Auto-detect source language if not provided
        if not source_lang:
            detection = await self.detect_language(text)
            source_lang = detection.language
        
        # In production, use translation API:
        # from google.cloud import translate_v2 as translate
        # client = translate.Client()
        # result = client.translate(text, target_language=target_lang, source_language=source_lang)
        # translated_text = result['translatedText']
        
        logger.info(f"Translating from {source_lang} to {target_lang}")
        
        # Simulated translation
        if source_lang == target_lang:
            translated_text = text
            confidence = 1.0
        else:
            # Simulated: prepend language indicator
            translated_text = f"[{target_lang.upper()}] {text}"
            confidence = 0.92
        
        # Detect topics
        topics = self._extract_topics(text)
        
        # Generate alternatives (simulated)
        alternatives = [
            f"Alternative 1: {translated_text}",
            f"Alternative 2: {translated_text}"
        ][:2]
        
        result = Translation(
            original_text=text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=confidence,
            alternatives=alternatives,
            detected_topics=topics
        )
        
        # Cache result
        self.translation_cache[cache_key] = result
        
        return result
    
    async def detect_language(self, text: str) -> LanguageDetection:
        """
        Detect language of text.
        
        Args:
            text: Input text
            
        Returns:
            Language detection result
        """
        # In production, use language detection library:
        # from langdetect import detect, detect_langs
        # lang = detect(text)
        # probs = detect_langs(text)
        
        logger.info("Detecting language")
        
        # Simulated detection based on character patterns
        text_lower = text.lower()
        
        if any(char in text for char in ['你', '我', '是']):
            lang = "zh"
            lang_name = "Chinese"
            confidence = 0.95
        elif any(char in text for char in ['の', 'は', 'を']):
            lang = "ja"
            lang_name = "Japanese"
            confidence = 0.94
        elif any(char in text for char in ['한', '국', '어']):
            lang = "ko"
            lang_name = "Korean"
            confidence = 0.93
        elif any(word in text_lower.split() for word in ['the', 'is', 'and', 'a']):
            lang = "en"
            lang_name = "English"
            confidence = 0.88
        elif any(word in text_lower.split() for word in ['el', 'la', 'de', 'que']):
            lang = "es"
            lang_name = "Spanish"
            confidence = 0.85
        else:
            lang = "en"
            lang_name = "English"
            confidence = 0.70
        
        alternatives = [
            ("en", 0.70),
            ("es", 0.15),
            ("fr", 0.10)
        ]
        
        return LanguageDetection(
            language=lang,
            language_name=lang_name,
            confidence=confidence,
            alternatives=alternatives
        )
    
    async def localize(
        self,
        content: Dict[str, str],
        target_locale: str
    ) -> LocalizedContent:
        """
        Full content localization with cultural adaptation.
        
        Args:
            content: Content dict (key -> text)
            target_locale: Target locale (e.g., 'en-US', 'fr-FR')
            
        Returns:
            Localized content with rules applied
        """
        logger.info(f"Localizing content to {target_locale}")
        
        # Parse locale
        lang = target_locale.split('-')[0] if '-' in target_locale else target_locale
        
        # Apply localization rules
        localized = {}
        applied_rules = []
        
        for key, text in content.items():
            # Translate text
            translation = await self.translate(text, target_lang=lang)
            localized[key] = translation.translated_text
            applied_rules.append(f"Translated '{key}' to {lang}")
        
        # Locale-specific formatting
        date_format, currency_symbol, number_format = self._get_locale_formats(target_locale)
        
        return LocalizedContent(
            content=localized,
            locale=target_locale,
            applied_rules=applied_rules,
            date_format=date_format,
            currency_symbol=currency_symbol,
            number_format=number_format
        )
    
    async def batch_translate(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> List[Translation]:
        """
        Translate multiple texts efficiently.
        
        Args:
            texts: List of texts to translate
            target_lang: Target language
            source_lang: Source language (auto-detect if None)
            
        Returns:
            List of translations
        """
        logger.info(f"Batch translating {len(texts)} texts")
        
        # In production, use batch API for efficiency
        translations = []
        
        for text in texts:
            translation = await self.translate(text, source_lang, target_lang)
            translations.append(translation)
        
        return translations
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        # Simplified topic extraction
        topics = []
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['business', 'company', 'market']):
            topics.append('business')
        
        if any(word in text_lower for word in ['technology', 'software', 'computer']):
            topics.append('technology')
        
        if any(word in text_lower for word in ['medical', 'health', 'patient']):
            topics.append('medical')
        
        if any(word in text_lower for word in ['legal', 'law', 'contract']):
            topics.append('legal')
        
        return topics or ['general']
    
    def _get_locale_formats(self, locale: str) -> Tuple[str, str, str]:
        """Get locale-specific formats"""
        locale_formats = {
            'en-US': ('MM/DD/YYYY', '$', '1,000.00'),
            'en-GB': ('DD/MM/YYYY', '£', '1,000.00'),
            'fr-FR': ('DD/MM/YYYY', '€', '1 000,00'),
            'de-DE': ('DD.MM.YYYY', '€', '1.000,00'),
            'zh-CN': ('YYYY-MM-DD', '¥', '1,000.00'),
            'ja-JP': ('YYYY/MM/DD', '¥', '1,000'),
        }
        
        return locale_formats.get(
            locale,
            ('DD/MM/YYYY', '$', '1,000.00')  # Default
        )


# Register agent
def create_translator_agent(agent_id: str = "translator") -> TranslatorAgent:
    """Create Translator Agent instance"""
    return TranslatorAgent(
        agent_id=agent_id,
        name="Translator",
        description="Expert in multilingual translation and localization"
    )
