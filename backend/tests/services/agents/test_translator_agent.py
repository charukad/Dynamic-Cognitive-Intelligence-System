"""
Unit Tests for Translator Agent

Tests all capabilities:
- Multi-language translation
- Language detection
- Cultural localization
- Batch translation
- Translation memory
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.services.agents.translator_agent import TranslatorAgent


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent():
    """Create Translator Agent instance"""
    return TranslatorAgent()


@pytest.fixture
def sample_texts():
    """Sample texts in different languages"""
    return {
        'en': "Hello, how are you?",
        'es': "Hola, ¿cómo estás?",
        'fr': "Bonjour, comment allez-vous?",
        'de': "Hallo, wie geht es dir?",
        'zh': "你好，你好吗？",
        'ja': "こんにちは、お元気ですか？"
    }


# ============================================================================
# Translation Tests
# ============================================================================

class TestTranslation:
    """Test translation capabilities"""
    
    @pytest.mark.asyncio
    async def test_basic_translation(self, agent):
        """Test basic text translation"""
        result = await agent.translate(
            text="Hello, world!",
            source_language="en",
            target_language="es"
        )
        
        assert 'translation' in result
        assert result['source_language'] == 'en'
        assert result['target_language'] == 'es'
        assert len(result['translation']) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_languages(self, agent, sample_texts):
        """Test translation to multiple target languages"""
        source_text = sample_texts['en']
        targets = ['es', 'fr', 'de', 'zh', 'ja']
        
        for target_lang in targets:
            result = await agent.translate(
                text=source_text,
                source_language='en',
                target_language=target_lang
            )
            
            assert result['target_language'] == target_lang
            assert len(result['translation']) > 0
    
    @pytest.mark.asyncio
    async def test_context_aware_translation(self, agent):
        """Test context-aware translation"""
        # "Bank" can mean financial institution or river bank
        result1 = await agent.translate(
            text="I went to the bank to deposit money",
            source_language="en",
            target_language="es",
            context="finance"
        )
        
        result2 = await agent.translate(
            text="I sat on the bank of the river",
            source_language="en",
            target_language="es",
            context="geography"
        )
        
        # Translations should be different
        assert result1['translation'] != result2['translation']


# ============================================================================
# Language Detection Tests
# ============================================================================

class TestLanguageDetection:
    """Test language detection"""
    
    @pytest.mark.asyncio
    async def test_detect_english(self, agent, sample_texts):
        """Test English detection"""
        result = await agent.detect_language(sample_texts['en'])
        
        assert result['language'] == 'en'
        assert result['confidence'] > 0.9
    
    @pytest.mark.asyncio
    async def test_detect_multiple_languages(self, agent, sample_texts):
        """Test detection of multiple languages"""
        expected = {
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'zh': 'zh',
            'ja': 'ja'
        }
        
        for expected_lang, text in sample_texts.items():
            result = await agent.detect_language(text)
            assert result['language'] == expected[expected_lang]
    
    @pytest.mark.asyncio
    async def test_detect_with_confidence(self, agent):
        """Test confidence scores"""
        result = await agent.detect_language(
            "This is a very clear English sentence with many words."
        )
        
        assert result['confidence'] > 0.95  # Very confident


# ============================================================================
# Localization Tests
# ============================================================================

class TestLocalization:
    """Test cultural localization"""
   
    @pytest.mark.asyncio
    async def test_date_localization(self, agent):
        """Test date format localization"""
        result = await agent.localize(
            text="The meeting is on 12/25/2024",
            target_region="en-GB"  # British English
        )
        
        assert '25/12/2024' in result['localized_text'] or '25 December' in result['localized_text']
    
    @pytest.mark.asyncio
    async def test_currency_localization(self, agent):
        """Test currency localization"""
        result = await agent.localize(
            text="The price is $100",
            target_region="en-GB"
        )
        
        assert 'localized_text' in result
    
    @pytest.mark.asyncio
    async def test_cultural_phrases(self, agent):
        """Test cultural phrase adaptation"""
        result = await agent.localize(
            text="It's raining cats and dogs",
            target_language="es",
            adapt_idioms=True
        )
        
        assert 'localized_text' in result
        # Should adapt the idiom, not translate literally


# ============================================================================
# Batch Translation Tests
# ============================================================================

class TestBatchTranslation:
    """Test batch translation"""
    
    @pytest.mark.asyncio
    async def test_batch_translate(self, agent):
        """Test translating multiple texts"""
        texts = [
            "Hello, world!",
            "How are you?",
            "Thank you very much."
        ]
        
        result = await agent.batch_translate(
            texts=texts,
            source_language="en",
            target_language="es"
        )
        
        assert 'translations' in result
        assert len(result['translations']) == 3
        assert all(t['translation'] for t in result['translations'])
    
    @pytest.mark.asyncio
    async def test_batch_preserve_order(self, agent):
        """Test that batch translation preserves order"""
        texts = ["First", "Second", "Third"]
        
        result = await agent.batch_translate(
            texts=texts,
            source_language="en",
            target_language="fr"
        )
        
        # Order should be preserved
        for i, translation in enumerate(result['translations']):
            assert translation['index'] == i


# ============================================================================
# Translation Memory Tests
# ============================================================================

class TestTranslationMemory:
    """Test translation memory/caching"""
    
    @pytest.mark.asyncio
    async def test_memory_caching(self, agent):
        """Test that repeated translations use cache"""
        text = "Hello, world!"
        
        # First translation
        result1 = await agent.translate(
            text=text,
            source_language="en",
            target_language="es"
        )
        
        # Second translation (should use cache)
        result2 = await agent.translate(
            text=text,
            source_language="en",
            target_language="es"
        )
        
        assert result1['translation'] == result2['translation']
        if 'from_cache' in result2:
            assert result2['from_cache'] is True
    
    @pytest.mark.asyncio
    async def test_memory_suggestions(self, agent):
        """Test translation memory suggestions"""
        # Translate similar phrase
        await agent.translate(
            text="Hello, world!",
            source_language="en",
            target_language="es"
        )
        
        # Get suggestions for similar text
        result = await agent.get_memory_suggestions(
            text="Hello, everyone!",
            source_language="en",
            target_language="es"
        )
        
        assert 'suggestions' in result


# ============================================================================
# Language Support Tests
# ============================================================================

class TestLanguageSupport:
    """Test supported languages"""
    
    @pytest.mark.asyncio
    async def test_get_supported_languages(self, agent):
        """Test retrieving supported languages"""
        result = await agent.get_supported_languages()
        
        assert 'languages' in result
        assert len(result['languages']) >= 50  # Should support many languages
        
        # Check common languages are supported
        common_langs = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ar', 'ru']
        for lang in common_langs:
            assert lang in result['languages']
    
    @pytest.mark.asyncio
    async def test_language_info(self, agent):
        """Test language information"""
        result = await agent.get_language_info('es')
        
        assert 'code' in result
        assert 'name' in result
        assert result['code'] == 'es'


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_full_translation_workflow(self, agent):
        """Test complete translation workflow"""
        # 1. Detect language
        text = "Hello, how are you?"
        detection = await agent.detect_language(text)
        assert detection['language'] == 'en'
        
        # 2. Translate
        translation = await agent.translate(
            text=text,
            source_language=detection['language'],
            target_language='es'
        )
        assert translation['translation']
        
        # 3. Localize
        localized = await agent.localize(
            text=translation['translation'],
            target_region='es-MX'  # Mexican Spanish
        )
        assert localized['localized_text']


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_text(self, agent):
        """Test translation of empty text"""
        with pytest.raises(ValueError):
            await agent.translate(
                text="",
                source_language="en",
                target_language="es"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_language_code(self, agent):
        """Test invalid language code"""
        with pytest.raises(ValueError):
            await agent.translate(
                text="Hello",
                source_language="invalid",
                target_language="es"
            )
    
    @pytest.mark.asyncio
    async def test_same_source_target(self, agent):
        """Test translation to same language"""
        # Should either return original or slight variation
        result = await agent.translate(
            text="Hello, world!",
            source_language="en",
            target_language="en"
        )
        
        assert result['translation']
