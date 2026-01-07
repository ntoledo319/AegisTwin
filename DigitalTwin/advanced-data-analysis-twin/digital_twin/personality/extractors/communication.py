"""
Communication Trait Extractor for the Digital Twin.

This module provides functionality for extracting personality traits from
communication data (emails, messages, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from ..traits import PersonalityTraitExtractor

logger = logging.getLogger(__name__)


class CommunicationTraitExtractor(PersonalityTraitExtractor):
    """
    Extractor for personality traits from communication data.
    """

    async def extract_traits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract personality traits from communication data.

        Args:
            data: Communication data dictionary containing messages, emails, etc.

        Returns:
            Dictionary of extracted traits
        """
        traits = {}

        # Extract messages from data
        messages = data.get("messages", [])
        emails = data.get("emails", [])
        
        if not messages and not emails:
            logger.warning("No communication data found")
            return traits

        # Process messages
        if messages:
            message_traits = await self._process_messages(messages)
            traits.update(message_traits)

        # Process emails
        if emails:
            email_traits = await self._process_emails(emails)
            
            # Combine traits from messages and emails
            for trait, value in email_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        logger.debug(f"Extracted {len(traits)} traits from communication data")
        return traits

    async def _process_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process messages to extract traits.

        Args:
            messages: List of message dictionaries

        Returns:
            Dictionary of extracted traits
        """
        if not messages:
            return {}

        # Initialize metrics
        total_messages = len(messages)
        total_words = 0
        total_chars = 0
        response_times = []
        emoji_count = 0
        question_count = 0
        exclamation_count = 0
        formal_count = 0
        informal_count = 0
        positive_sentiment = 0
        negative_sentiment = 0
        initiation_count = 0  # Number of conversations initiated by user
        
        # Time of day distribution
        time_distribution = {
            "morning": 0,    # 5:00 - 11:59
            "afternoon": 0,  # 12:00 - 16:59
            "evening": 0,    # 17:00 - 21:59
            "night": 0       # 22:00 - 4:59
        }
        
        # Process each message
        for i, message in enumerate(messages):
            content = message.get("content", "")
            timestamp = message.get("timestamp")
            is_sender = message.get("is_sender", False)
            
            # Skip if no content
            if not content:
                continue
                
            # Count words and characters
            words = content.split()
            total_words += len(words)
            total_chars += len(content)
            
            # Count emojis (simplified)
            emoji_count += len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]', content))
            
            # Count questions and exclamations
            question_count += content.count('?')
            exclamation_count += content.count('!')
            
            # Check formality
            formal_indicators = self._count_matches(content, self._get_formal_indicators())
            informal_indicators = self._count_matches(content, self._get_informal_indicators())
            formal_count += formal_indicators
            informal_count += informal_indicators
            
            # Check sentiment
            positive_words = self._count_matches(content, self._get_positive_words())
            negative_words = self._count_matches(content, self._get_negative_words())
            positive_sentiment += positive_words
            negative_sentiment += negative_words
            
            # Check if user initiated the conversation
            if i > 0 and is_sender:
                prev_message = messages[i-1]
                prev_timestamp = prev_message.get("timestamp")
                
                if timestamp and prev_timestamp:
                    try:
                        curr_time = datetime.fromisoformat(timestamp)
                        prev_time = datetime.fromisoformat(prev_timestamp)
                        time_diff = (curr_time - prev_time).total_seconds() / 3600  # hours
                        
                        # If more than 3 hours have passed, consider it a new conversation
                        if time_diff > 3:
                            initiation_count += 1
                    except (ValueError, TypeError):
                        pass
            elif i == 0 and is_sender:
                initiation_count += 1
                
            # Calculate response time
            if i > 0 and is_sender:
                prev_message = messages[i-1]
                if not prev_message.get("is_sender", True):  # If previous message is from other person
                    curr_timestamp = message.get("timestamp")
                    prev_timestamp = prev_message.get("timestamp")
                    
                    if curr_timestamp and prev_timestamp:
                        try:
                            curr_time = datetime.fromisoformat(curr_timestamp)
                            prev_time = datetime.fromisoformat(prev_timestamp)
                            response_time = (curr_time - prev_time).total_seconds() / 60  # minutes
                            
                            # Only consider reasonable response times (less than 24 hours)
                            if 0 < response_time < 1440:
                                response_times.append(response_time)
                        except (ValueError, TypeError):
                            pass
            
            # Track time of day distribution
            if timestamp:
                try:
                    msg_time = datetime.fromisoformat(timestamp)
                    hour = msg_time.hour
                    
                    if 5 <= hour < 12:
                        time_distribution["morning"] += 1
                    elif 12 <= hour < 17:
                        time_distribution["afternoon"] += 1
                    elif 17 <= hour < 22:
                        time_distribution["evening"] += 1
                    else:
                        time_distribution["night"] += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate derived metrics
        avg_words_per_message = total_words / max(1, total_messages)
        avg_chars_per_word = total_chars / max(1, total_words)
        avg_response_time = sum(response_times) / max(1, len(response_times))
        emoji_rate = emoji_count / max(1, total_words) * 100
        question_rate = question_count / max(1, total_messages)
        exclamation_rate = exclamation_count / max(1, total_messages)
        
        total_formality_indicators = formal_count + informal_count
        formality_score = formal_count / max(1, total_formality_indicators)
        
        total_sentiment_words = positive_sentiment + negative_sentiment
        sentiment_score = positive_sentiment / max(1, total_sentiment_words)
        
        initiation_rate = initiation_count / max(1, len(messages) / 10)  # Normalize by conversation chunks
        
        # Determine preferred time of day
        total_time_messages = sum(time_distribution.values())
        time_preferences = {time: count / max(1, total_time_messages) for time, count in time_distribution.items()}
        preferred_time = max(time_preferences, key=time_preferences.get)
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion(
            initiation_rate, 
            avg_response_time,
            emoji_rate,
            avg_words_per_message
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness(
            avg_response_time,
            formality_score,
            preferred_time == "morning"
        )
        
        # Agreeableness traits
        traits["agreeableness"] = self._calculate_agreeableness(
            sentiment_score,
            question_rate,
            emoji_rate
        )
        
        # Neuroticism traits
        traits["neuroticism"] = self._calculate_neuroticism(
            sentiment_score,
            exclamation_rate,
            avg_response_time
        )
        
        # Openness traits
        traits["openness"] = self._calculate_openness(
            avg_words_per_message,
            avg_chars_per_word,
            question_rate
        )
        
        # Communication style traits
        traits["formality"] = formality_score
        traits["verbosity"] = self._calculate_verbosity(avg_words_per_message)
        traits["emotionality"] = self._calculate_emotionality(sentiment_score, exclamation_rate, emoji_rate)
        traits["responsiveness"] = self._calculate_responsiveness(avg_response_time)
        traits["assertiveness"] = self._calculate_assertiveness(initiation_rate, exclamation_rate)
        
        return traits

    async def _process_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process emails to extract traits.

        Args:
            emails: List of email dictionaries

        Returns:
            Dictionary of extracted traits
        """
        # Similar to _process_messages but adapted for email format
        # For brevity, we'll implement a simplified version
        
        if not emails:
            return {}
            
        # Initialize metrics
        total_emails = len(emails)
        total_words = 0
        formal_count = 0
        informal_count = 0
        greeting_count = 0
        signature_count = 0
        
        for email in emails:
            content = email.get("content", "")
            subject = email.get("subject", "")
            
            # Skip if no content
            if not content:
                continue
                
            # Count words
            words = content.split()
            total_words += len(words)
            
            # Check formality
            formal_indicators = self._count_matches(content, self._get_formal_indicators())
            informal_indicators = self._count_matches(content, self._get_informal_indicators())
            formal_count += formal_indicators
            informal_count += informal_indicators
            
            # Check for greetings and signatures
            if re.search(r'^(Dear|Hello|Hi|Greetings|Good morning|Good afternoon|Good evening)', content, re.MULTILINE):
                greeting_count += 1
                
            if re.search(r'(Sincerely|Best regards|Regards|Thanks|Thank you|Yours truly|Cheers|Best wishes)', content, re.MULTILINE):
                signature_count += 1
        
        # Calculate derived metrics
        avg_words_per_email = total_words / max(1, total_emails)
        
        total_formality_indicators = formal_count + informal_count
        formality_score = formal_count / max(1, total_formality_indicators)
        
        greeting_rate = greeting_count / max(1, total_emails)
        signature_rate = signature_count / max(1, total_emails)
        
        # Map metrics to personality traits
        traits = {}
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._normalize_trait_value(
            formality_score * 0.5 + 
            greeting_rate * 0.25 + 
            signature_rate * 0.25
        )
        
        # Communication style traits
        traits["formality"] = formality_score
        traits["verbosity"] = self._calculate_verbosity(avg_words_per_email)
        traits["professionalism"] = self._normalize_trait_value(
            formality_score * 0.6 + 
            greeting_rate * 0.2 + 
            signature_rate * 0.2
        )
        
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

    def _calculate_extraversion(self, initiation_rate: float, avg_response_time: float, 
                               emoji_rate: float, avg_words_per_message: float) -> float:
        """
        Calculate extraversion score from communication metrics.

        Args:
            initiation_rate: Rate of conversation initiation
            avg_response_time: Average response time in minutes
            emoji_rate: Rate of emoji usage
            avg_words_per_message: Average words per message

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        # Convert response time to a score (faster = higher extraversion)
        response_time_score = 1.0 - min(1.0, avg_response_time / 120)  # Normalize to 2 hours max
        
        # Calculate extraversion score
        extraversion_score = (
            initiation_rate * 0.4 +
            response_time_score * 0.2 +
            min(1.0, emoji_rate / 10) * 0.2 +
            min(1.0, avg_words_per_message / 50) * 0.2
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_conscientiousness(self, avg_response_time: float, formality_score: float, 
                                    morning_person: bool) -> float:
        """
        Calculate conscientiousness score from communication metrics.

        Args:
            avg_response_time: Average response time in minutes
            formality_score: Formality score
            morning_person: Whether the person is active in the morning

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        # Convert response time to a score (moderate = higher conscientiousness)
        # Too fast might indicate impulsivity, too slow might indicate procrastination
        response_time_score = 1.0 - abs(avg_response_time - 30) / 30
        response_time_score = max(0.0, min(1.0, response_time_score))
        
        # Calculate conscientiousness score
        conscientiousness_score = (
            response_time_score * 0.3 +
            formality_score * 0.5 +
            (0.2 if morning_person else 0.0)
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_agreeableness(self, sentiment_score: float, question_rate: float, 
                               emoji_rate: float) -> float:
        """
        Calculate agreeableness score from communication metrics.

        Args:
            sentiment_score: Sentiment score
            question_rate: Rate of questions asked
            emoji_rate: Rate of emoji usage

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        # Calculate agreeableness score
        agreeableness_score = (
            sentiment_score * 0.5 +
            min(1.0, question_rate) * 0.3 +
            min(1.0, emoji_rate / 10) * 0.2
        )
        
        return self._normalize_trait_value(agreeableness_score)

    def _calculate_neuroticism(self, sentiment_score: float, exclamation_rate: float, 
                             avg_response_time: float) -> float:
        """
        Calculate neuroticism score from communication metrics.

        Args:
            sentiment_score: Sentiment score
            exclamation_rate: Rate of exclamation marks
            avg_response_time: Average response time in minutes

        Returns:
            Neuroticism score (0.0 to 1.0)
        """
        # Invert sentiment score (higher negativity = higher neuroticism)
        negative_sentiment = 1.0 - sentiment_score
        
        # Convert response time to a score (very fast or very slow = higher neuroticism)
        response_time_factor = abs(avg_response_time - 30) / 30
        response_time_score = min(1.0, response_time_factor)
        
        # Calculate neuroticism score
        neuroticism_score = (
            negative_sentiment * 0.5 +
            min(1.0, exclamation_rate) * 0.3 +
            response_time_score * 0.2
        )
        
        return self._normalize_trait_value(neuroticism_score)

    def _calculate_openness(self, avg_words_per_message: float, avg_chars_per_word: float, 
                          question_rate: float) -> float:
        """
        Calculate openness score from communication metrics.

        Args:
            avg_words_per_message: Average words per message
            avg_chars_per_word: Average characters per word
            question_rate: Rate of questions asked

        Returns:
            Openness score (0.0 to 1.0)
        """
        # Calculate openness score
        openness_score = (
            min(1.0, avg_words_per_message / 50) * 0.4 +
            min(1.0, avg_chars_per_word / 6) * 0.3 +
            min(1.0, question_rate) * 0.3
        )
        
        return self._normalize_trait_value(openness_score)

    def _calculate_verbosity(self, avg_words_per_message: float) -> float:
        """
        Calculate verbosity score from communication metrics.

        Args:
            avg_words_per_message: Average words per message

        Returns:
            Verbosity score (0.0 to 1.0)
        """
        # Calculate verbosity score
        verbosity_score = min(1.0, avg_words_per_message / 50)
        
        return self._normalize_trait_value(verbosity_score)

    def _calculate_emotionality(self, sentiment_score: float, exclamation_rate: float, 
                              emoji_rate: float) -> float:
        """
        Calculate emotionality score from communication metrics.

        Args:
            sentiment_score: Sentiment score
            exclamation_rate: Rate of exclamation marks
            emoji_rate: Rate of emoji usage

        Returns:
            Emotionality score (0.0 to 1.0)
        """
        # High emotionality can be either positive or negative
        # What matters is the intensity and density of emotional expressions
        sentiment_intensity = abs(sentiment_score - 0.5) * 2
        
        # Calculate emotionality score
        emotionality_score = (
            sentiment_intensity * 0.4 +
            min(1.0, exclamation_rate) * 0.3 +
            min(1.0, emoji_rate / 10) * 0.3
        )
        
        return self._normalize_trait_value(emotionality_score)

    def _calculate_responsiveness(self, avg_response_time: float) -> float:
        """
        Calculate responsiveness score from communication metrics.

        Args:
            avg_response_time: Average response time in minutes

        Returns:
            Responsiveness score (0.0 to 1.0)
        """
        # Convert response time to a score (faster = higher responsiveness)
        # Use an exponential decay function
        responsiveness_score = 1.0 * (2.0 ** (-avg_response_time / 60))
        
        return self._normalize_trait_value(responsiveness_score)

    def _calculate_assertiveness(self, initiation_rate: float, exclamation_rate: float) -> float:
        """
        Calculate assertiveness score from communication metrics.

        Args:
            initiation_rate: Rate of conversation initiation
            exclamation_rate: Rate of exclamation marks

        Returns:
            Assertiveness score (0.0 to 1.0)
        """
        # Calculate assertiveness score
        assertiveness_score = (
            initiation_rate * 0.7 +
            min(1.0, exclamation_rate) * 0.3
        )
        
        return self._normalize_trait_value(assertiveness_score)