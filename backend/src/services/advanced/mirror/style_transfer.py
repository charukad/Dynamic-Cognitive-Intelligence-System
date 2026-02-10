"""
Style Transfer - Capture and replicate communication patterns

Analyzes and models user's unique communication style including:
- Vocabulary preferences
- Sentence structure patterns  
- Punctuation usage
- Response length distribution
"""

from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import re
import statistics


class StyleTransfer:
    """Capture user's communication style for replication"""
    
    def __init__(self):
        """Initialize style analyzer"""
        self.punctuation_pattern = re.compile(r'[.!?,;:]')
        self.emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F]')  # Emoticons
        self.sentence_enders = {'.', '!', '?'}
    
    def extract_style(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract communication style signature from messages.
        
        Args:
            messages: List of user messages
        
        Returns:
            Style profile with patterns and preferences
        """
        if not messages:
            return self._empty_style()
        
        user_messages = [
            msg for msg in messages 
            if msg.get('role') in ['user', 'human']
        ]
        
        if not user_messages:
            return self._empty_style()
        
        return {
            'vocabulary': self._analyze_vocabulary(user_messages),
            'sentence_structure': self._analyze_sentence_structure(user_messages),
            'punctuation': self._analyze_punctuation(user_messages),
            'length_distribution': self._analyze_length_distribution(user_messages),
            'stylistic_markers': self._extract_stylistic_markers(user_messages),
        }
    
    def _analyze_vocabulary(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze vocabulary preferences and patterns"""
        all_words = []
        word_freq = Counter()
        
        for msg in messages:
            content = msg.get('content', '').lower()
            # Remove punctuation for word counting
            words = re.sub(r'[^\w\s]', '', content).split()
            all_words.extend(words)
            word_freq.update(words)
        
        # Vocabulary richness (unique words / total words)
        unique_words = len(set(all_words))
        total_words = len(all_words)
        vocab_richness = unique_words / total_words if total_words > 0 else 0
        
        # Most common words (excluding stop words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
        }
        
        signature_words = [
            {'word': word, 'count': count}
            for word, count in word_freq.most_common(50)
            if word not in stop_words and len(word) > 2
        ][:20]  # Top 20 signature words
        
        return {
            'vocab_richness': round(vocab_richness, 3),
            'unique_words': unique_words,
            'total_words': total_words,
            'signature_words': signature_words,
        }
    
    def _analyze_sentence_structure(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze sentence patterns and structure"""
        sentence_lengths = []
        question_ratio = 0
        exclamation_ratio = 0
        total_sentences = 0
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            for sentence in sentences:
                words = sentence.split()
                sentence_lengths.append(len(words))
                total_sentences += 1
                
                # Check sentence type
                if '?' in sentence:
                    question_ratio += 1
                if '!' in sentence:
                    exclamation_ratio += 1
        
        if total_sentences == 0:
            return self._empty_sentence_structure()
        
        return {
            'avg_sentence_length': round(statistics.mean(sentence_lengths), 1) if sentence_lengths else 0,
            'median_sentence_length': statistics.median(sentence_lengths) if sentence_lengths else 0,
            'sentence_length_stddev': round(statistics.stdev(sentence_lengths), 1) if len(sentence_lengths) > 1 else 0,
            'question_ratio': round(question_ratio / total_sentences, 3),
            'exclamation_ratio': round(exclamation_ratio / total_sentences, 3),
            'total_sentences': total_sentences,
        }
    
    def _analyze_punctuation(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze punctuation usage patterns"""
        punct_counts = Counter()
        total_chars = 0
        
        for msg in messages:
            content = msg.get('content', '')
            total_chars += len(content)
            
            # Count punctuation
            for char in content:
                if char in '.!?,;:-…':
                    punct_counts[char] += 1
        
        # Calculate punctuation density
        total_punct = sum(punct_counts.values())
        punct_density = total_punct / total_chars if total_chars > 0 else 0
        
        return {
            'punctuation_density': round(punct_density, 4),
            'period_count': punct_counts.get('.', 0),
            'question_count': punct_counts.get('?', 0),
            'exclamation_count': punct_counts.get('!', 0),
            'comma_count': punct_counts.get(',', 0),
            'semicolon_count': punct_counts.get(';', 0),
            'ellipsis_count': punct_counts.get('…', 0) + content.count('...'),
        }
    
    def _analyze_length_distribution(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze message length distribution"""
        lengths = []
        
        for msg in messages:
            content = msg.get('content', '')
            word_count = len(content.split())
            char_count = len(content)
            lengths.append({
                'words': word_count,
                'chars': char_count,
            })
        
        if not lengths:
            return {'message_count': 0}
        
        word_lengths = [l['words'] for l in lengths]
        char_lengths = [l['chars'] for l in lengths]
        
        return {
            'avg_words_per_message': round(statistics.mean(word_lengths), 1),
            'median_words_per_message': statistics.median(word_lengths),
            'avg_chars_per_message': round(statistics.mean(char_lengths), 1),
            'message_count': len(lengths),
            'shortest_message_words': min(word_lengths),
            'longest_message_words': max(word_lengths),
        }
    
    def _extract_stylistic_markers(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extract unique stylistic markers"""
        all_content = ' '.join(msg.get('content', '') for msg in messages)
        
        # Count various markers
        markers = {
            'uses_contractions': self._count_contractions(all_content),
            'uses_abbreviations': self._count_abbreviations(all_content),
            'uses_all_caps': len(re.findall(r'\b[A-Z]{2,}\b', all_content)),
            'uses_ellipsis': all_content.count('...') + all_content.count('…'),
            'uses_parentheses': all_content.count('('),
            'uses_quotes': all_content.count('"') + all_content.count("'"),
            'paragraph_breaks': all_content.count('\n\n'),
        }
        
        return markers
    
    def _count_contractions(self, text: str) -> int:
        """Count contractions like don't, can't, etc."""
        contractions = [
            "don't", "doesn't", "didn't", "can't", "couldn't", "won't", 
            "wouldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't",
            "haven't", "hasn't", "hadn't", "i'm", "you're", "he's", "she's",
            "it's", "we're", "they're", "i've", "you've", "we've", "they've",
        ]
        
        text_lower = text.lower()
        return sum(text_lower.count(contraction) for contraction in contractions)
    
    def _count_abbreviations(self, text: str) -> int:
        """Count common abbreviations"""
        abbreviations = ['etc', 'e.g', 'i.e', 'vs', 'aka', 'fyi', 'btw', 'imho']
        text_lower = text.lower()
        return sum(text_lower.count(abbr) for abbr in abbreviations)
    
    def _empty_style(self) -> Dict[str, Any]:
        """Return empty style profile"""
        return {
            'vocabulary': {
                'vocab_richness': 0.0,
                'unique_words': 0,
                'total_words': 0,
                'signature_words': [],
            },
            'sentence_structure': self._empty_sentence_structure(),
            'punctuation': {
                'punctuation_density': 0.0,
                'period_count': 0,
                'question_count': 0,
                'exclamation_count': 0,
                'comma_count': 0,
            },
            'length_distribution': {
                'message_count': 0,
            },
            'stylistic_markers': {},
        }
    
    def _empty_sentence_structure(self) -> Dict[str, Any]:
        """Return empty sentence structure"""
        return {
            'avg_sentence_length': 0.0,
            'median_sentence_length': 0,
            'question_ratio': 0.0,
            'exclamation_ratio': 0.0,
            'total_sentences': 0,
        }
