"""
Textual Trait Extractor for the Digital Twin.

This module provides functionality for extracting personality traits from
textual data.
"""

import logging
from typing import Dict, Any, List, Optional
import re

from ..traits import PersonalityTraitExtractor

logger = logging.getLogger(__name__)


class TextualTraitExtractor(PersonalityTraitExtractor):
    """
    Extractor for personality traits from textual data.
    """

    async def extract_traits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract personality traits from textual data.

        Args:
            data: Textual data dictionary

        Returns:
            Dictionary of extracted traits
        """
        traits = {}

        # Extract content from data
        content = data.get("content", "")
        if not content:
            logger.warning("No content found in textual data")
            return traits

        # Extract basic text metrics
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))
        avg_word_length = sum(len(word) for word in content.split()) / max(1, word_count)
        avg_sentence_length = word_count / max(1, sentence_count)

        # Extract vocabulary richness
        unique_words = set(word.lower() for word in re.findall(r'\b\w+\b', content))
        vocabulary_richness = len(unique_words) / max(1, word_count)

        # Extract sentiment indicators
        positive_words = self._count_matches(content, self._get_positive_words())
        negative_words = self._count_matches(content, self._get_negative_words())
        total_sentiment_words = positive_words + negative_words
        sentiment_score = positive_words / max(1, total_sentiment_words)

        # Extract formality indicators
        formal_indicators = self._count_matches(content, self._get_formal_indicators())
        informal_indicators = self._count_matches(content, self._get_informal_indicators())
        total_formality_indicators = formal_indicators + informal_indicators
        formality_score = formal_indicators / max(1, total_formality_indicators)

        # Extract analytical thinking indicators
        analytical_indicators = self._count_matches(content, self._get_analytical_indicators())
        analytical_score = min(1.0, analytical_indicators / max(1, word_count / 100))

        # Map text metrics to personality traits
        traits["openness"] = self._calculate_openness(vocabulary_richness, avg_sentence_length, analytical_score)
        traits["conscientiousness"] = self._calculate_conscientiousness(avg_sentence_length, formality_score)
        traits["extraversion"] = self._calculate_extraversion(word_count, sentiment_score)
        traits["agreeableness"] = self._calculate_agreeableness(sentiment_score, formality_score)
        traits["neuroticism"] = self._calculate_neuroticism(sentiment_score)

        # Add communication style traits
        traits["formality"] = formality_score
        traits["verbosity"] = self._calculate_verbosity(word_count, avg_sentence_length)
        traits["emotionality"] = self._calculate_emotionality(sentiment_score, total_sentiment_words / max(1, word_count))
        traits["assertiveness"] = self._calculate_assertiveness(content)
        traits["analytical_thinking"] = analytical_score

        logger.debug(f"Extracted {len(traits)} traits from textual data")
        return traits

    def _count_matches(self, text: str, patterns: List[str]) -> int:
        """
        Count the number of matches for a list of patterns in text.

        Args:
            text: Text to search
            patterns: List of patterns to match

        Returns:
            Number of matches
        """
        count = 0
        for pattern in patterns:
            count += len(re.findall(r'\b' + re.escape(pattern) + r'\b', text.lower()))
        return count

    def _get_positive_words(self) -> List[str]:
        """
        Get a list of positive sentiment words.

        Returns:
            List of positive words
        """
        # This is a small sample list for demonstration
        return [
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "happy", "joy", "love", "like", "best", "beautiful", "perfect",
            "awesome", "brilliant", "outstanding", "superb", "terrific"
        ]

    def _get_negative_words(self) -> List[str]:
        """
        Get a list of negative sentiment words.

        Returns:
            List of negative words
        """
        # This is a small sample list for demonstration
        return [
            "bad", "terrible", "awful", "horrible", "poor", "worst",
            "sad", "angry", "hate", "dislike", "disappointing", "ugly",
            "stupid", "boring", "annoying", "frustrating", "dreadful"
        ]

    def _get_formal_indicators(self) -> List[str]:
        """
        Get a list of formal language indicators.

        Returns:
            List of formal indicators
        """
        # This is a small sample list for demonstration
        return [
            "therefore", "however", "nevertheless", "furthermore", "consequently",
            "regarding", "concerning", "additionally", "moreover", "thus",
            "hereby", "accordingly", "subsequently", "aforementioned", "pursuant"
        ]

    def _get_informal_indicators(self) -> List[str]:
        """
        Get a list of informal language indicators.

        Returns:
            List of informal indicators
        """
        # This is a small sample list for demonstration
        return [
            "yeah", "nah", "cool", "awesome", "stuff", "things", "kinda",
            "sorta", "gonna", "wanna", "gotta", "dunno", "ain't", "y'all",
            "lol", "omg", "btw", "idk", "tbh", "fyi", "asap"
        ]

    def _get_analytical_indicators(self) -> List[str]:
        """
        Get a list of analytical thinking indicators.

        Returns:
            List of analytical indicators
        """
        # This is a small sample list for demonstration
        return [
            "analyze", "analysis", "consider", "comparison", "evaluate",
            "evidence", "research", "study", "data", "conclusion", "therefore",
            "hypothesis", "theory", "experiment", "observation", "methodology",
            "result", "correlation", "causation", "implication", "inference"
        ]

    def _calculate_openness(self, vocabulary_richness: float, avg_sentence_length: float, analytical_score: float) -> float:
        """
        Calculate openness score from text metrics.

        Args:
            vocabulary_richness: Vocabulary richness score
            avg_sentence_length: Average sentence length
            analytical_score: Analytical thinking score

        Returns:
            Openness score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        openness_score = (vocabulary_richness * 0.5 + 
                         min(1.0, avg_sentence_length / 20) * 0.2 + 
                         analytical_score * 0.3)
        return self._normalize_trait_value(openness_score)

    def _calculate_conscientiousness(self, avg_sentence_length: float, formality_score: float) -> float:
        """
        Calculate conscientiousness score from text metrics.

        Args:
            avg_sentence_length: Average sentence length
            formality_score: Formality score

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        conscientiousness_score = (min(1.0, avg_sentence_length / 15) * 0.3 + 
                                  formality_score * 0.7)
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_extraversion(self, word_count: int, sentiment_score: float) -> float:
        """
        Calculate extraversion score from text metrics.

        Args:
            word_count: Word count
            sentiment_score: Sentiment score

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        verbosity_score = min(1.0, word_count / 500)
        extraversion_score = (verbosity_score * 0.6 + 
                             sentiment_score * 0.4)
        return self._normalize_trait_value(extraversion_score)

    def _calculate_agreeableness(self, sentiment_score: float, formality_score: float) -> float:
        """
        Calculate agreeableness score from text metrics.

        Args:
            sentiment_score: Sentiment score
            formality_score: Formality score

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        agreeableness_score = (sentiment_score * 0.7 + 
                              (1 - formality_score) * 0.3)
        return self._normalize_trait_value(agreeableness_score)

    def _calculate_neuroticism(self, sentiment_score: float) -> float:
        """
        Calculate neuroticism score from text metrics.

        Args:
            sentiment_score: Sentiment score

        Returns:
            Neuroticism score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        # Invert sentiment score (higher negativity = higher neuroticism)
        neuroticism_score = 1.0 - sentiment_score
        return self._normalize_trait_value(neuroticism_score)

    def _calculate_verbosity(self, word_count: int, avg_sentence_length: float) -> float:
        """
        Calculate verbosity score from text metrics.

        Args:
            word_count: Word count
            avg_sentence_length: Average sentence length

        Returns:
            Verbosity score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        verbosity_score = (min(1.0, word_count / 500) * 0.7 + 
                          min(1.0, avg_sentence_length / 20) * 0.3)
        return self._normalize_trait_value(verbosity_score)

    def _calculate_emotionality(self, sentiment_score: float, sentiment_density: float) -> float:
        """
        Calculate emotionality score from text metrics.

        Args:
            sentiment_score: Sentiment score
            sentiment_density: Density of sentiment words

        Returns:
            Emotionality score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        # High emotionality can be either positive or negative
        # What matters is the intensity and density of emotional words
        emotionality_score = (abs(sentiment_score - 0.5) * 2 * 0.4 + 
                             min(1.0, sentiment_density * 5) * 0.6)
        return self._normalize_trait_value(emotionality_score)

    def _calculate_assertiveness(self, content: str) -> float:
        """
        Calculate assertiveness score from text content.

        Args:
            content: Text content

        Returns:
            Assertiveness score (0.0 to 1.0)
        """
        # This is a simplified calculation for demonstration
        # Count assertive phrases and imperative sentences
        assertive_phrases = [
            "i believe", "i think", "i know", "i am confident", "i am sure",
            "certainly", "definitely", "absolutely", "must", "should", "will"
        ]
        
        assertive_count = self._count_matches(content, assertive_phrases)
        
        # Count imperative sentences (starting with a verb)
        sentences = re.split(r'[.!?]+', content)
        imperative_count = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and re.match(r'^[A-Z]?[a-z]+\b', sentence):
                first_word = sentence.split()[0].lower()
                if first_word in ["do", "go", "try", "make", "take", "get", "find", "use",
                                 "start", "stop", "avoid", "keep", "let", "please", "remember"]:
                    imperative_count += 1
        
        total_sentences = max(1, len(sentences))
        imperative_ratio = imperative_count / total_sentences
        
        assertiveness_score = (min(1.0, assertive_count / 10) * 0.6 + 
                              imperative_ratio * 0.4)
        
        return self._normalize_trait_value(assertiveness_score)