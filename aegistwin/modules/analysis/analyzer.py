"""
AegisTwin Analyzer

Entity extraction, relationship detection, and sentiment analysis.

@ai_prompt: Use Analyzer.analyze() to extract insights from normalized data.
@context_boundary: aegistwin/modules/analysis/analyzer

# AI-GENERATED 2026-01-06
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter
import re


@dataclass
class AnalysisResult:
    """Result of analysis."""
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    topics: List[str]
    sentiment: Dict[str, float]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """Extracted entity."""
    type: str
    value: str
    count: int = 1
    context: Optional[str] = None


@dataclass
class Relationship:
    """Detected relationship between entities."""
    source: str
    target: str
    type: str
    weight: float = 1.0


class Analyzer:
    """
    Analyzer for extracting entities, relationships, and insights.
    
    Performs:
    - Named entity recognition (basic pattern-based)
    - Relationship detection
    - Topic extraction
    - Sentiment analysis (lexicon-based)
    """
    
    # Simple sentiment lexicons
    POSITIVE_WORDS = {
        "good", "great", "excellent", "amazing", "wonderful", "fantastic",
        "love", "happy", "glad", "thanks", "thank", "awesome", "perfect",
        "beautiful", "brilliant", "nice", "pleased", "delighted", "excited",
    }
    
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "horrible", "hate", "sad", "angry",
        "frustrated", "disappointed", "annoyed", "upset", "sorry", "wrong",
        "fail", "failed", "problem", "issue", "error", "broken", "worst",
    }
    
    # Common topics/themes
    TOPIC_PATTERNS = {
        "work": r"\b(work|job|office|meeting|project|deadline|boss|colleague)\b",
        "family": r"\b(family|mom|dad|parent|child|kid|brother|sister|son|daughter)\b",
        "health": r"\b(health|doctor|sick|medicine|hospital|exercise|gym|diet)\b",
        "travel": r"\b(travel|trip|vacation|flight|hotel|airport|visit)\b",
        "food": r"\b(food|eat|dinner|lunch|breakfast|restaurant|cook|meal)\b",
        "technology": r"\b(tech|computer|phone|app|software|code|programming)\b",
        "finance": r"\b(money|bank|pay|cost|price|budget|invest|save)\b",
        "social": r"\b(friend|party|event|birthday|wedding|celebrate)\b",
    }
    
    def __init__(self):
        self._entity_extractors = [
            self._extract_persons,
            self._extract_organizations,
            self._extract_locations,
            self._extract_dates,
        ]
    
    def analyze(
        self,
        records: List[Dict[str, Any]],
        analysis_type: str = "full",
    ) -> AnalysisResult:
        """
        Analyze records to extract entities, relationships, and insights.
        
        Args:
            records: Normalized records to analyze
            analysis_type: Type of analysis (full, entities, sentiment, topics)
            
        Returns:
            AnalysisResult with extracted information
        """
        # Collect all text content
        texts = self._collect_texts(records)
        combined_text = " ".join(texts)
        
        # Extract entities
        entities = []
        if analysis_type in ("full", "entities"):
            entities = self._extract_all_entities(texts)
        
        # Detect relationships
        relationships = []
        if analysis_type in ("full", "entities"):
            relationships = self._detect_relationships(records, entities)
        
        # Extract topics
        topics = []
        if analysis_type in ("full", "topics"):
            topics = self._extract_topics(combined_text)
        
        # Analyze sentiment
        sentiment = {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
        if analysis_type in ("full", "sentiment"):
            sentiment = self._analyze_sentiment(combined_text)
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(records, entities, topics)
        
        return AnalysisResult(
            entities=[{"type": e.type, "value": e.value, "count": e.count} for e in entities],
            relationships=[
                {"source": r.source, "target": r.target, "type": r.type, "weight": r.weight}
                for r in relationships
            ],
            topics=topics,
            sentiment=sentiment,
            confidence=confidence,
            metadata={
                "record_count": len(records),
                "text_length": len(combined_text),
                "analysis_type": analysis_type,
            },
        )
    
    def _collect_texts(self, records: List[Dict[str, Any]]) -> List[str]:
        """Collect text content from records."""
        texts = []
        text_fields = ["content", "text", "message", "body", "subject"]
        
        for record in records:
            for field in text_fields:
                if field in record and isinstance(record[field], str):
                    texts.append(record[field])
        
        return texts
    
    def _extract_all_entities(self, texts: List[str]) -> List[Entity]:
        """Extract all entity types from texts."""
        all_entities = []
        
        for extractor in self._entity_extractors:
            entities = extractor(texts)
            all_entities.extend(entities)
        
        # Deduplicate and count
        entity_counts: Dict[Tuple[str, str], int] = Counter()
        for entity in all_entities:
            key = (entity.type, entity.value.lower())
            entity_counts[key] += 1
        
        return [
            Entity(type=t, value=v.title(), count=c)
            for (t, v), c in entity_counts.most_common()
        ]
    
    def _extract_persons(self, texts: List[str]) -> List[Entity]:
        """Extract person names (basic heuristic)."""
        entities = []
        # Pattern: Capitalized words that look like names
        name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
        
        # Common non-name words to exclude
        exclude = {
            "I", "The", "This", "That", "What", "When", "Where", "Why", "How",
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
            "January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December",
        }
        
        for text in texts:
            matches = re.findall(name_pattern, text)
            for match in matches:
                if match not in exclude and len(match) > 2:
                    entities.append(Entity(type="person", value=match))
        
        return entities
    
    def _extract_organizations(self, texts: List[str]) -> List[Entity]:
        """Extract organization names."""
        entities = []
        # Pattern: Words ending in common suffixes
        org_pattern = r"\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\s+(?:Inc|Corp|LLC|Ltd|Company|Co|Foundation)\.?)\b"
        
        for text in texts:
            matches = re.findall(org_pattern, text)
            for match in matches:
                entities.append(Entity(type="organization", value=match))
        
        return entities
    
    def _extract_locations(self, texts: List[str]) -> List[Entity]:
        """Extract location mentions."""
        entities = []
        # Common location indicators
        location_pattern = r"\b(?:in|at|from|to|near)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b"
        
        for text in texts:
            matches = re.findall(location_pattern, text)
            for match in matches:
                entities.append(Entity(type="location", value=match))
        
        return entities
    
    def _extract_dates(self, texts: List[str]) -> List[Entity]:
        """Extract date mentions."""
        entities = []
        date_patterns = [
            r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?)\b",
        ]
        
        for text in texts:
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    entities.append(Entity(type="date", value=match))
        
        return entities
    
    def _detect_relationships(
        self,
        records: List[Dict[str, Any]],
        entities: List[Entity],
    ) -> List[Relationship]:
        """Detect relationships between entities."""
        relationships = []
        
        # Look for sender/receiver patterns
        for record in records:
            sender = record.get("sender") or record.get("from") or record.get("sender_id")
            receiver = record.get("receiver") or record.get("to") or record.get("receiver_id")
            
            if sender and receiver:
                relationships.append(Relationship(
                    source=str(sender),
                    target=str(receiver),
                    type="communicates_with",
                ))
        
        # Co-occurrence in same record suggests relationship
        person_entities = [e for e in entities if e.type == "person"]
        if len(person_entities) >= 2:
            for i, e1 in enumerate(person_entities[:5]):
                for e2 in person_entities[i+1:6]:
                    relationships.append(Relationship(
                        source=e1.value,
                        target=e2.value,
                        type="mentioned_with",
                        weight=0.5,
                    ))
        
        return relationships
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        topics = []
        text_lower = text.lower()
        
        for topic, pattern in self.TOPIC_PATTERNS.items():
            if re.search(pattern, text_lower):
                topics.append(topic)
        
        return topics[:5]  # Limit to top 5 topics
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using lexicon-based approach."""
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
        
        positive_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
        
        positive_ratio = positive_count / total_sentiment_words
        negative_ratio = negative_count / total_sentiment_words
        neutral_ratio = max(0, 1 - (positive_ratio + negative_ratio) * 2)
        
        # Normalize
        total = positive_ratio + negative_ratio + neutral_ratio
        return {
            "positive": round(positive_ratio / total, 2),
            "neutral": round(neutral_ratio / total, 2),
            "negative": round(negative_ratio / total, 2),
        }
    
    def _calculate_confidence(
        self,
        records: List[Dict[str, Any]],
        entities: List[Entity],
        topics: List[str],
    ) -> float:
        """Calculate confidence score for the analysis."""
        confidence = 0.5  # Base confidence
        
        # More records = higher confidence
        if len(records) >= 10:
            confidence += 0.2
        elif len(records) >= 5:
            confidence += 0.1
        
        # Found entities = higher confidence
        if len(entities) >= 5:
            confidence += 0.15
        elif len(entities) >= 2:
            confidence += 0.1
        
        # Found topics = higher confidence
        if len(topics) >= 2:
            confidence += 0.1
        elif len(topics) >= 1:
            confidence += 0.05
        
        return min(0.95, round(confidence, 2))
