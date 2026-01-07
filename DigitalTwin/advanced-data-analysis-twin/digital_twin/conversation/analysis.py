"""
Conversation Analyzer for the Digital Twin's Conversation Engine.

This module provides functionality for analyzing user messages, including
intent detection, sentiment analysis, topic extraction, and entity recognition.
"""

import logging
import re
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class ConversationAnalyzer:
    """
    Analyzer for conversation messages.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the conversation analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.nlp_provider = self.config.get("nlp_provider", "spacy")
        self.nlp_model = self.config.get("nlp_model", "en_core_web_sm")
        self.nlp = None
        self._initialize_nlp()
        logger.info("Conversation Analyzer initialized")

    def _initialize_nlp(self) -> None:
        """
        Initialize NLP library for text analysis.
        """
        try:
            # Try to import spaCy
            import spacy
            
            # Try to load the model
            try:
                self.nlp = spacy.load(self.nlp_model)
                logger.info(f"Loaded spaCy model: {self.nlp_model}")
            except OSError:
                # Model not found, try to download it
                logger.warning(f"spaCy model {self.nlp_model} not found, attempting to download")
                try:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "spacy", "download", self.nlp_model])
                    self.nlp = spacy.load(self.nlp_model)
                    logger.info(f"Downloaded and loaded spaCy model: {self.nlp_model}")
                except Exception as e:
                    logger.error(f"Error downloading spaCy model: {str(e)}")
                    self.nlp = None
                    
        except ImportError:
            logger.warning("spaCy not available, using fallback text analysis")
            self.nlp = None

    async def analyze_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a user message.

        Args:
            message: User message
            context: Conversation context

        Returns:
            Analysis results
        """
        # Initialize analysis results
        analysis = {
            "intent": await self._detect_intent(message),
            "sentiment": await self._analyze_sentiment(message),
            "topics": await self._extract_topics(message, context),
            "entities": await self._extract_entities(message),
            "question_type": await self._detect_question_type(message),
            "complexity": await self._analyze_complexity(message),
            "urgency": await self._detect_urgency(message),
            "formality": await self._analyze_formality(message)
        }
        
        logger.debug(f"Analyzed message: intent={analysis['intent']}, sentiment={analysis['sentiment']}")
        return analysis

    async def _detect_intent(self, message: str) -> str:
        """
        Detect the intent of a message.

        Args:
            message: User message

        Returns:
            Intent string
        """
        # This is a simplified implementation
        # In a real implementation, this would use a more sophisticated intent detection system
        
        # Check for question intent
        if "?" in message or message.lower().startswith(("what", "who", "when", "where", "why", "how", "can", "could", "would", "will", "is", "are", "do", "does", "did")):
            return "question"
            
        # Check for greeting intent
        greeting_patterns = ["hello", "hi ", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        if any(pattern in message.lower() for pattern in greeting_patterns):
            return "greeting"
            
        # Check for farewell intent
        farewell_patterns = ["goodbye", "bye", "see you", "talk to you later", "have a good day", "until next time"]
        if any(pattern in message.lower() for pattern in farewell_patterns):
            return "goodbye"
            
        # Check for thank you intent
        thank_patterns = ["thank you", "thanks", "appreciate it", "grateful"]
        if any(pattern in message.lower() for pattern in thank_patterns):
            return "thank_you"
            
        # Check for help intent
        help_patterns = ["help", "assist", "support", "guide", "explain", "clarify"]
        if any(pattern in message.lower() for pattern in help_patterns):
            return "help"
            
        # Check for request intent
        request_patterns = ["can you", "could you", "would you", "will you", "please", "I need", "I want", "I'd like"]
        if any(pattern in message.lower() for pattern in request_patterns):
            return "request"
            
        # Default to statement intent
        return "statement"

    async def _analyze_sentiment(self, message: str) -> str:
        """
        Analyze the sentiment of a message.

        Args:
            message: User message

        Returns:
            Sentiment string (positive, negative, or neutral)
        """
        # This is a simplified implementation
        # In a real implementation, this would use a more sophisticated sentiment analysis system
        
        # Load sentiment lexicons
        positive_words = [
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "happy", "joy", "love", "like", "best", "beautiful", "perfect",
            "awesome", "brilliant", "outstanding", "superb", "terrific",
            "pleased", "delighted", "glad", "satisfied", "enjoy", "excited"
        ]
        
        negative_words = [
            "bad", "terrible", "awful", "horrible", "poor", "worst",
            "sad", "angry", "hate", "dislike", "disappointing", "ugly",
            "stupid", "boring", "annoying", "frustrating", "dreadful",
            "upset", "unhappy", "disappointed", "irritated", "furious"
        ]
        
        # Count sentiment words
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    async def _extract_topics(self, message: str, context: Dict[str, Any]) -> List[str]:
        """
        Extract topics from a message.

        Args:
            message: User message
            context: Conversation context

        Returns:
            List of topics
        """
        # This is a simplified implementation
        # In a real implementation, this would use a more sophisticated topic extraction system
        
        # If spaCy is available, use it
        if self.nlp:
            try:
                # Process the message
                doc = self.nlp(message)
                
                # Extract noun phrases as potential topics
                topics = [chunk.text.lower() for chunk in doc.noun_chunks]
                
                # Filter out common pronouns and short phrases
                filtered_topics = [topic for topic in topics if len(topic) > 3 and topic not in ["this", "that", "these", "those", "it", "they", "them"]]
                
                # Limit to top 3 topics
                return filtered_topics[:3]
            except Exception as e:
                logger.error(f"Error extracting topics with spaCy: {str(e)}")
                
        # Fallback: Extract potential topics based on capitalized words and noun patterns
        words = message.split()
        potential_topics = []
        
        # Look for capitalized words (potential proper nouns)
        for word in words:
            if word[0].isupper() and len(word) > 3 and word.lower() not in ["i", "i'm", "i'll", "i've", "i'd"]:
                potential_topics.append(word.lower())
                
        # Look for words that often indicate topics
        topic_indicators = ["about", "regarding", "concerning", "on the subject of", "related to", "talking about"]
        for indicator in topic_indicators:
            if indicator in message.lower():
                # Get the words after the indicator
                parts = message.lower().split(indicator, 1)
                if len(parts) > 1:
                    # Take the next few words as a potential topic
                    after_indicator = parts[1].strip().split()[:3]
                    if after_indicator:
                        potential_topics.append(" ".join(after_indicator))
                        
        # If no topics found, use the current topic from context
        if not potential_topics and "current_topic" in context and context["current_topic"]:
            return [context["current_topic"]]
            
        # Limit to top 3 topics
        return potential_topics[:3]

    async def _extract_entities(self, message: str) -> List[str]:
        """
        Extract entities from a message.

        Args:
            message: User message

        Returns:
            List of entities
        """
        # This is a simplified implementation
        # In a real implementation, this would use a more sophisticated entity extraction system
        
        # If spaCy is available, use it
        if self.nlp:
            try:
                # Process the message
                doc = self.nlp(message)
                
                # Extract named entities
                entities = [ent.text for ent in doc.ents]
                
                # Limit to top 5 entities
                return entities[:5]
            except Exception as e:
                logger.error(f"Error extracting entities with spaCy: {str(e)}")
                
        # Fallback: Extract potential entities based on capitalized words
        words = message.split()
        potential_entities = []
        
        # Look for capitalized words (potential proper nouns)
        for i in range(len(words)):
            if words[i][0].isupper() and words[i].lower() not in ["i", "i'm", "i'll", "i've", "i'd"]:
                # Check if it's part of a multi-word entity
                entity = [words[i]]
                j = i + 1
                while j < len(words) and words[j][0].isupper():
                    entity.append(words[j])
                    j += 1
                    
                potential_entities.append(" ".join(entity))
                
        # Limit to top 5 entities
        return potential_entities[:5]

    async def _detect_question_type(self, message: str) -> str:
        """
        Detect the type of question in a message.

        Args:
            message: User message

        Returns:
            Question type string
        """
        # Check if it's a question
        if "?" not in message and not message.lower().startswith(("what", "who", "when", "where", "why", "how", "can", "could", "would", "will", "is", "are", "do", "does", "did")):
            return "not_question"
            
        # Detect question type
        message_lower = message.lower()
        
        if message_lower.startswith(("what", "which")):
            return "what"
        elif message_lower.startswith("who"):
            return "who"
        elif message_lower.startswith("when"):
            return "when"
        elif message_lower.startswith("where"):
            return "where"
        elif message_lower.startswith("why"):
            return "why"
        elif message_lower.startswith("how"):
            return "how"
        elif message_lower.startswith(("can", "could", "would", "will")):
            return "yes_no"
        elif message_lower.startswith(("is", "are", "do", "does", "did")):
            return "yes_no"
        else:
            return "other_question"

    async def _analyze_complexity(self, message: str) -> str:
        """
        Analyze the complexity of a message.

        Args:
            message: User message

        Returns:
            Complexity string (simple, medium, or complex)
        """
        # Count words and sentences
        words = message.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', message)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Calculate average sentence length
        if sentence_count > 0:
            avg_sentence_length = word_count / sentence_count
        else:
            avg_sentence_length = word_count
            
        # Calculate lexical diversity
        unique_words = set(word.lower() for word in words)
        lexical_diversity = len(unique_words) / max(1, word_count)
        
        # Determine complexity
        if word_count < 10 or (avg_sentence_length < 8 and lexical_diversity < 0.7):
            return "simple"
        elif word_count > 30 or (avg_sentence_length > 15 or lexical_diversity > 0.8):
            return "complex"
        else:
            return "medium"

    async def _detect_urgency(self, message: str) -> str:
        """
        Detect the urgency of a message.

        Args:
            message: User message

        Returns:
            Urgency string (high, medium, or low)
        """
        # Look for urgency indicators
        high_urgency_patterns = [
            "urgent", "emergency", "immediately", "asap", "right now",
            "critical", "crisis", "hurry", "quickly", "fast"
        ]
        
        medium_urgency_patterns = [
            "soon", "today", "tomorrow", "need", "important",
            "priority", "attention", "timely"
        ]
        
        message_lower = message.lower()
        
        # Check for high urgency
        if any(pattern in message_lower for pattern in high_urgency_patterns):
            return "high"
            
        # Check for medium urgency
        if any(pattern in message_lower for pattern in medium_urgency_patterns):
            return "medium"
            
        # Default to low urgency
        return "low"

    async def _analyze_formality(self, message: str) -> str:
        """
        Analyze the formality of a message.

        Args:
            message: User message

        Returns:
            Formality string (formal, neutral, or informal)
        """
        # Look for formality indicators
        formal_indicators = [
            "would you please", "I would like to", "I am", "thank you",
            "sincerely", "regards", "dear", "respectfully", "kindly"
        ]
        
        informal_indicators = [
            "hey", "hi", "yeah", "nah", "cool", "awesome", "stuff", "things",
            "kinda", "sorta", "gonna", "wanna", "gotta", "dunno", "ain't",
            "y'all", "lol", "omg", "btw", "idk", "tbh", "fyi", "asap"
        ]
        
        message_lower = message.lower()
        
        # Count indicators
        formal_count = sum(1 for indicator in formal_indicators if indicator in message_lower)
        informal_count = sum(1 for indicator in informal_indicators if indicator in message_lower)
        
        # Check for contractions (informal)
        contraction_count = len(re.findall(r"\b\w+'\w+\b", message_lower))
        informal_count += contraction_count
        
        # Determine formality
        if formal_count > informal_count:
            return "formal"
        elif informal_count > formal_count:
            return "informal"
        else:
            return "neutral"

    async def analyze_conversation_history(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a conversation history.

        Args:
            history: List of conversation messages

        Returns:
            Analysis results
        """
        # Initialize analysis results
        analysis = {
            "message_count": len(history),
            "user_messages": 0,
            "system_messages": 0,
            "average_user_message_length": 0,
            "average_system_message_length": 0,
            "sentiment_trend": "neutral",
            "common_topics": [],
            "common_entities": []
        }
        
        # Count messages by role
        user_messages = [msg for msg in history if msg.get("role") == "user"]
        system_messages = [msg for msg in history if msg.get("role") == "system"]
        
        analysis["user_messages"] = len(user_messages)
        analysis["system_messages"] = len(system_messages)
        
        # Calculate average message lengths
        if user_messages:
            user_message_lengths = [len(msg.get("content", "")) for msg in user_messages]
            analysis["average_user_message_length"] = sum(user_message_lengths) / len(user_messages)
            
        if system_messages:
            system_message_lengths = [len(msg.get("content", "")) for msg in system_messages]
            analysis["average_system_message_length"] = sum(system_message_lengths) / len(system_messages)
            
        # Analyze sentiment trend
        if user_messages:
            sentiments = []
            for msg in user_messages:
                sentiment = await self._analyze_sentiment(msg.get("content", ""))
                sentiments.append(sentiment)
                
            # Count sentiment occurrences
            positive_count = sentiments.count("positive")
            negative_count = sentiments.count("negative")
            neutral_count = sentiments.count("neutral")
            
            # Determine overall sentiment trend
            if positive_count > negative_count and positive_count > neutral_count:
                analysis["sentiment_trend"] = "positive"
            elif negative_count > positive_count and negative_count > neutral_count:
                analysis["sentiment_trend"] = "negative"
            else:
                analysis["sentiment_trend"] = "neutral"
                
        # Extract common topics and entities
        all_topics = []
        all_entities = []
        
        for msg in user_messages:
            content = msg.get("content", "")
            topics = await self._extract_topics(content, {})
            entities = await self._extract_entities(content)
            
            all_topics.extend(topics)
            all_entities.extend(entities)
            
        # Count occurrences of topics and entities
        from collections import Counter
        
        topic_counter = Counter(all_topics)
        entity_counter = Counter(all_entities)
        
        # Get most common topics and entities
        analysis["common_topics"] = [topic for topic, count in topic_counter.most_common(5)]
        analysis["common_entities"] = [entity for entity, count in entity_counter.most_common(5)]
        
        logger.debug(f"Analyzed conversation history: {len(history)} messages")
        return analysis

    async def detect_conversation_patterns(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect patterns in a conversation history.

        Args:
            history: List of conversation messages

        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Check for repetitive questions
        user_messages = [msg.get("content", "") for msg in history if msg.get("role") == "user"]
        if len(user_messages) >= 3:
            # Check for repeated questions
            question_count = sum(1 for msg in user_messages if "?" in msg)
            if question_count / len(user_messages) > 0.7:
                patterns.append({
                    "type": "repetitive_questions",
                    "description": "User is asking multiple questions in succession",
                    "confidence": 0.8
                })
                
        # Check for topic switching
        if len(user_messages) >= 4:
            topics_by_message = []
            for msg in user_messages:
                topics = await self._extract_topics(msg, {})
                topics_by_message.append(topics)
                
            # Check if topics change frequently
            topic_changes = 0
            for i in range(1, len(topics_by_message)):
                if not any(topic in topics_by_message[i-1] for topic in topics_by_message[i]):
                    topic_changes += 1
                    
            if topic_changes / (len(topics_by_message) - 1) > 0.5:
                patterns.append({
                    "type": "frequent_topic_switching",
                    "description": "User is frequently changing conversation topics",
                    "confidence": 0.7
                })
                
        # Check for sentiment shifts
        if len(user_messages) >= 4:
            sentiments = []
            for msg in user_messages:
                sentiment = await self._analyze_sentiment(msg)
                sentiments.append(sentiment)
                
            # Check for sentiment shifts
            sentiment_shifts = 0
            for i in range(1, len(sentiments)):
                if sentiments[i] != sentiments[i-1]:
                    sentiment_shifts += 1
                    
            if sentiment_shifts / (len(sentiments) - 1) > 0.5:
                patterns.append({
                    "type": "sentiment_volatility",
                    "description": "User's sentiment is changing frequently",
                    "confidence": 0.6
                })
                
        # Check for increasing message length
        if len(user_messages) >= 3:
            message_lengths = [len(msg) for msg in user_messages]
            increasing = True
            for i in range(1, len(message_lengths)):
                if message_lengths[i] <= message_lengths[i-1]:
                    increasing = False
                    break
                    
            if increasing:
                patterns.append({
                    "type": "increasing_verbosity",
                    "description": "User's messages are becoming increasingly verbose",
                    "confidence": 0.7
                })
                
        logger.debug(f"Detected {len(patterns)} conversation patterns")
        return patterns