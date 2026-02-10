"""
Mirror Protocol Tests

Tests for digital twin creation and management.
"""

import pytest
from src.services.advanced.mirror import (
    PersonaExtractor,
    StyleTransfer,
    PersonalityModel,
    MirrorService,
)


# Sample message data
@pytest.fixture
def sample_messages():
    """Sample user messages for testing"""
    return [
        {"role": "user", "content": "Can you help me understand Python decorators? I'm curious about the implementation.", "timestamp": "2024-01-01T10:00:00Z"},
        {"role": "assistant", "content": "Of course! Decorators are...", "timestamp": "2024-01-01T10:01:00Z"},
        {"role": "user", "content": "That's interesting! How do I create a custom decorator?", "timestamp": "2024-01-01T10:02:00Z"},
        {"role": "assistant", "content": "To create a custom decorator...", "timestamp": "2024-01-01T10:03:00Z"},
        {"role": "user", "content": "I see. Could you show me an example with arguments?", "timestamp": "2024-01-01T10:04:00Z"},
        {"role": "user", "content": "Also, what's the difference between function and class decorators?", "timestamp": "2024-01-01T10:05:00Z"},
        {"role": "user", "content": "Thanks for the help! This is really useful. I appreciate your clear explanations.", "timestamp": "2024-01-01T10:06:00Z"},
        {"role": "user", "content": "By the way, do you know any good resources for learning Python design patterns?", "timestamp": "2024-01-01T10:07:00Z"},
        {"role": "user", "content": "Great! I'll check those out. I really enjoy learning new programming concepts.", "timestamp": "2024-01-01T10:08:00Z"},
        {"role": "user", "content": "One more thing - how would you compare Python to JavaScript for backend development?", "timestamp": "2024-01-01T10:09:00Z"},
        {"role": "user", "content": "That makes sense. I'm working on a data science project, so Python is perfect.", "timestamp": "2024-01-01T10:10:00Z"},
        {"role": "user", "content": "Do you have experience with machine learning libraries like scikit-learn?", "timestamp": "2024-01-01T10:11:00Z"},
        {"role": "user", "content": "Excellent! Could you explain the difference between supervised and unsupervised learning?", "timestamp": "2024-01-01T10:12:00Z"},
        {"role": "user", "content": "I'd love to build a classification model. What algorithm should I start with?", "timestamp": "2024-01-01T10:13:00Z"},
        {"role": "user", "content": "Thanks! This has been super helpful. I feel much more confident now.", "timestamp": "2024-01-01T10:14:00Z"},
    ]


@pytest.fixture
def casual_messages():
    """Casual communication style messages"""
    return [
        {"role": "user", "content": "hey! what's up?"},
        {"role": "user", "content": "yeah that's cool"},
        {"role": "user", "content": "nah i don't think so"},
        {"role": "user", "content": "lol that's funny"},
        {"role": "user", "content": "awesome thanks!"},
        {"role": "user", "content": "ok cool"},
        {"role": "user", "content": "sounds good"},
        {"role": "user", "content": "yeah totally"},
        {"role": "user", "content": "hmm not sure"},
        {"role": "user", "content": "alright see ya"},
    ]


@pytest.fixture  
def formal_messages():
    """Formal communication style messages"""
    return [
        {"role": "user", "content": "Good morning. I would appreciate your assistance with this matter."},
        {"role": "user", "content": "Thank you kindly for your prompt response."},
        {"role": "user", "content": "Furthermore, I believe we should consider the following approach."},
        {"role": "user", "content": "Please let me know if you require any additional information."},
        {"role": "user", "content": "I sincerely appreciate your help with this complex issue."},
        {"role": "user", "content": "Nevertheless, I think we must proceed with caution."},
        {"role": "user", "content": "Could you kindly provide more details regarding this topic?"},
        {"role": "user", "content": "I look forward to your response at your earliest convenience."},
        {"role": "user", "content": "Thank you for your time and consideration."},
        {"role": "user", "content": "Regards, and have a pleasant day."},
    ]


# PersonaExtractor Tests
class TestPersonaExtractor:
    """Test persona extraction functionality"""
    
    def test_extract_persona_basic(self, sample_messages):
        """Test basic persona extraction"""
        extractor = PersonaExtractor()
        persona = extractor.extract_persona(sample_messages)
        
        assert 'communication_style' in persona
        assert 'knowledge_domains' in persona
        assert 'emotional_pattern' in persona
        assert 'decision_style' in persona
        assert 'confidence' in persona
    
    def test_communication_style_formal(self, formal_messages):
        """Test formal communication detection"""
        extractor = PersonaExtractor()
        persona = extractor.extract_persona(formal_messages)
        
        style = persona['communication_style']
        assert style['formality'] > 0.0  # Should detect formal language
    
    def test_communication_style_casual(self, casual_messages):
        """Test casual communication detection"""
        extractor = PersonaExtractor()
        persona = extractor.extract_persona(casual_messages)
        
        style = persona['communication_style']
        assert style['formality'] < 0.0  # Should detect casual language
    
    def test_knowledge_domains_extraction(self, sample_messages):
        """Test knowledge domain extraction"""
        extractor = PersonaExtractor()
        persona = extractor.extract_persona(sample_messages)
        
        domains = persona['knowledge_domains']
        assert len(domains) > 0
        # Should detect programming/data_science domains
        domain_names = [d['domain'] for d in domains]
        assert any(d in ['programming', 'data_science'] for d in domain_names)
    
    def test_emotional_pattern_positive(self, sample_messages):
        """Test emotional pattern detection"""
        extractor = PersonaExtractor()
        persona = extractor.extract_persona(sample_messages)
        
        emotion = persona['emotional_pattern']
        # Sample messages are generally positive
        assert emotion['sentiment_balance'] >= 0
    
    def test_confidence_score_scaling(self):
        """Test confidence score increases with message count"""
        extractor = PersonaExtractor()
        
        # 5 messages = low confidence
        few_msgs = [{"role": "user", "content": "test"}] * 5
        persona_few = extractor.extract_persona(few_msgs)
        
        # 100 messages = higher confidence
        many_msgs = [{"role": "user", "content": "test"}] * 100
        persona_many = extractor.extract_persona(many_msgs)
        
        assert persona_many['confidence'] > persona_few['confidence']
    
    def test_empty_messages(self):
        """Test handling of empty message list"""
        extractor = PersonaExtractor()
        persona = extractor.extract_persona([])
        
        assert persona['confidence'] == 0.0
        assert persona['interaction_stats']['total_messages'] == 0


# StyleTransfer Tests
class TestStyleTransfer:
    """Test style transfer functionality"""
    
    def test_extract_style_basic(self, sample_messages):
        """Test basic style extraction"""
        transfer = StyleTransfer()
        style = transfer.extract_style(sample_messages)
        
        assert 'vocabulary' in style
        assert 'sentence_structure' in style
        assert 'punctuation' in style
        assert 'length_distribution' in style
    
    def test_vocabulary_richness(self, sample_messages):
        """Test vocabulary richness calculation"""
        transfer = StyleTransfer()
        style = transfer.extract_style(sample_messages)
        
        vocab = style['vocabulary']
        assert 0 <= vocab['vocab_richness'] <= 1.0
        assert vocab['unique_words'] > 0
        assert vocab['total_words'] > 0
    
    def test_sentence_structure(self, sample_messages):
        """Test sentence structure analysis"""
        transfer = StyleTransfer()
        style = transfer.extract_style(sample_messages)
        
        structure = style['sentence_structure']
        assert structure['avg_sentence_length'] > 0
        assert structure['total_sentences'] > 0
    
    def test_punctuation_analysis(self, sample_messages):
        """Test punctuation pattern detection"""
        transfer = StyleTransfer()
        style = transfer.extract_style(sample_messages)
        
        punct = style['punctuation']
        assert 'punctuation_density' in punct
        assert punct['question_count'] > 0  # Sample has questions
    
    def test_length_distribution(self, sample_messages):
        """Test message length distribution"""
        transfer = StyleTransfer()
        style = transfer.extract_style(sample_messages)
        
        lengths = style['length_distribution']
        assert lengths['avg_words_per_message'] > 0
        assert lengths['message_count'] > 0


# PersonalityModel Tests
class TestPersonalityModel:
    """Test personality modeling functionality"""
    
    def test_build_ocean_profile(self, sample_messages):
        """Test OCEAN profile generation"""
        extractor = PersonaExtractor()
        transfer = StyleTransfer()
        model = PersonalityModel()
        
        persona = extractor.extract_persona(sample_messages)
        style = transfer.extract_style(sample_messages)
        ocean = model.build_ocean_profile(sample_messages, persona, style)
        
        # Check all traits present
        assert 'openness' in ocean
        assert 'conscientiousness' in ocean
        assert 'extraversion' in ocean
        assert 'agreeableness' in ocean
        assert 'neuroticism' in ocean
        
        # Check scores in valid range
        for trait, score in ocean.items():
            assert 0.0 <= score <= 1.0, f"{trait} score {score} out of range"
    
    def test_openness_detection(self, sample_messages):
        """Test openness trait detection"""
        extractor = PersonaExtractor()
        transfer = StyleTransfer()
        model = PersonalityModel()
        
        persona = extractor.extract_persona(sample_messages)
        style = transfer.extract_style(sample_messages)
        ocean = model.build_ocean_profile(sample_messages, persona, style)
        
        # Sample messages show curiosity and learning
        assert ocean['openness'] > 0.4
    
    def test_interpret_ocean(self):
        """Test OCEAN interpretation"""
        model = PersonalityModel()
        
        ocean = {
            'openness': 0.8,
            'conscientiousness': 0.3,
            'extraversion': 0.5,
            'agreeableness': 0.7,
            'neuroticism': 0.2,
        }
        
        interpretation = model.interpret_ocean(ocean)
        
        assert len(interpretation) == 5
        assert 'creative' in interpretation['openness'].lower() or 'creative' in interpretation['openness'].lower()


# MirrorService Tests
class TestMirrorService:
    """Test mirror service integration"""
    
    @pytest.mark.asyncio
    async def test_create_twin(self, sample_messages):
        """Test digital twin creation"""
        service = MirrorService()
        twin = await service.create_twin("user123", sample_messages)
        
        assert twin.user_id == "user123"
        assert twin.confidence_score > 0
        assert len(twin.knowledge_domains) > 0
        assert twin.interaction_count > 0
    
    @pytest.mark.asyncio
    async def test_get_twin(self, sample_messages):
        """Test twin retrieval"""
        service = MirrorService()
        
        # Create twin
        await service.create_twin("user123", sample_messages)
        
        # Retrieve twin
        twin = await service.get_twin("user123")
        assert twin is not None
        assert twin.user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_twin(self):
        """Test retrieving non-existent twin"""
        service = MirrorService()
        twin = await service.get_twin("nonexistent")
        assert twin is None
    
    @pytest.mark.asyncio
    async def test_delete_twin(self, sample_messages):
        """Test twin deletion"""
        service = MirrorService()
        
        # Create twin
        await service.create_twin("user123", sample_messages)
        
        # Delete twin
        success = await service.delete_twin("user123")
        assert success is True
        
        # Verify deleted
        twin = await service.get_twin("user123")
        assert twin is None
    
    @pytest.mark.asyncio
    async def test_simulate_response(self, sample_messages):
        """Test response simulation"""
        service = MirrorService()
        
        # Create twin
        await service.create_twin("user123", sample_messages)
        
        # Simulate response
        simulation = await service.simulate_response("user123", "What do you think about AI?")
        
        assert simulation is not None
        assert 'predicted_length_words' in simulation
        assert 'predicted_formality' in simulation
        assert 'likely_topics' in simulation
    
    @pytest.mark.asyncio
    async def test_accuracy_metrics(self, sample_messages):
        """Test accuracy metrics"""
        service = MirrorService()
        
        # Create twin
        await service.create_twin("user123", sample_messages)
        
        # Get metrics
        metrics = await service.get_twin_accuracy_metrics("user123")
        
        assert metrics is not None
        assert 'overall_confidence' in metrics
        assert 'recommended_actions' in metrics
    
    @pytest.mark.asyncio
    async def test_twin_to_dict(self, sample_messages):
        """Test twin dictionary serialization"""
        service = MirrorService()
        twin = await service.create_twin("user123", sample_messages)
        
        twin_dict = twin.to_dict()
        
        assert isinstance(twin_dict, dict)
        assert 'user_id' in twin_dict
        assert 'created_at' in twin_dict
        assert isinstance(twin_dict['created_at'], str)  # ISO format
