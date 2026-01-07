"""Memory modeling for MindMirror."""

import os
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import re
from collections import Counter, defaultdict
import json
from datetime import datetime, timedelta
import heapq

from ...core.config import config_manager
from ...core.utils import normalize_text, save_pickle, load_pickle, ensure_dir, extract_keywords, calculate_text_similarity

class MemoryModel:
    """Models episodic and semantic memory."""
    
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the memory model.
        
        Args:
            model_dir: Directory to store model data.
        """
        self.model_dir = model_dir or config_manager.get_value('mindmirror', 'data.model_dir', 'data/models')
        ensure_dir(self.model_dir)
        
        # Episodic memory (specific events/conversations)
        self.episodic_memory = []
        
        # Semantic memory (knowledge, facts, concepts)
        self.semantic_memory = {}
        
        # Entity memory (people, places, organizations)
        self.entity_memory = {}
        
        # Memory parameters
        self.memory_params = {
            'episodic_memory_size': config_manager.get_value('mindmirror', 'cognitive_model.memory.episodic_memory_size', 1000),
            'semantic_memory_size': config_manager.get_value('mindmirror', 'cognitive_model.memory.semantic_memory_size', 5000),
            'memory_decay_rate': config_manager.get_value('mindmirror', 'cognitive_model.memory.memory_decay_rate', 0.05),
            'important_memory_boost': config_manager.get_value('mindmirror', 'cognitive_model.memory.important_memory_boost', 5.0)
        }
        
        # Memory statistics
        self.memory_stats = {
            'total_episodic_memories': 0,
            'total_semantic_memories': 0,
            'total_entity_memories': 0,
            'memory_by_recency': {},
            'memory_by_importance': {}
        }
        
        # Loaded flag
        self.is_loaded = False
        
    def train(self, messages: List[Dict[str, Any]], user_name: Optional[str] = None) -> None:
        """Train the memory model on messages.
        
        Args:
            messages: List of messages to train on.
            user_name: Name of the user (to identify outgoing messages).
        """
        print("Training memory model...")
        
        # Process all messages for episodic memory
        self._build_episodic_memory(messages)
        
        # Extract semantic memory from messages
        self._build_semantic_memory(messages)
        
        # Extract entity memory
        self._build_entity_memory(messages)
        
        # Update memory statistics
        self._update_memory_stats()
        
        # Save the model
        self.save()
        
        self.is_loaded = True
        print("Memory model training complete")
        
    def _build_episodic_memory(self, messages: List[Dict[str, Any]]) -> None:
        """Build episodic memory from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        print("Building episodic memory...")
        
        # Group messages by conversation
        conversations = {}
        for message in messages:
            chat_session = message.get('chat_session', '')
            if not chat_session:
                continue
                
            if chat_session not in conversations:
                conversations[chat_session] = []
                
            conversations[chat_session].append(message)
            
        # Sort conversations by date
        for chat_session, chat_messages in conversations.items():
            conversations[chat_session] = sorted(
                chat_messages,
                key=lambda m: m.get('message_date', '')
            )
            
        # Extract episodic memories (conversation snippets)
        for chat_session, chat_messages in conversations.items():
            # Skip conversations with too few messages
            if len(chat_messages) < 3:
                continue
                
            # Process conversation in chunks
            chunk_size = 5  # Number of messages per memory
            overlap = 2  # Number of overlapping messages between chunks
            
            for i in range(0, len(chat_messages), chunk_size - overlap):
                chunk = chat_messages[i:i + chunk_size]
                
                # Skip chunks that are too small
                if len(chunk) < 3:
                    continue
                    
                # Extract memory data
                try:
                    first_date = datetime.strptime(chunk[0].get('message_date', ''), '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    first_date = None
                    
                # Extract participants
                participants = set()
                for msg in chunk:
                    if msg.get('type') == 'Incoming' and msg.get('sender_name'):
                        participants.add(msg.get('sender_name'))
                    elif msg.get('type') == 'Outgoing':
                        participants.add('self')
                        
                # Extract content
                content = []
                for msg in chunk:
                    sender = msg.get('sender_name', 'self') if msg.get('type') == 'Incoming' else 'self'
                    text = msg.get('text', '')
                    if text:
                        content.append(f"{sender}: {text}")
                        
                # Skip if no content
                if not content:
                    continue
                    
                # Create memory
                memory = {
                    'type': 'episodic',
                    'subtype': 'conversation',
                    'date': first_date,
                    'participants': list(participants),
                    'content': content,
                    'context': chat_session,
                    'importance': self._calculate_memory_importance(content, participants),
                    'last_accessed': datetime.now(),
                    'access_count': 0,
                    'keywords': extract_keywords(' '.join(content), 10)
                }
                
                self.episodic_memory.append(memory)
                
        # Sort episodic memories by date
        self.episodic_memory = sorted(
            self.episodic_memory,
            key=lambda m: m['date'] if m['date'] else datetime.min
        )
        
        # Limit episodic memory size
        if len(self.episodic_memory) > self.memory_params['episodic_memory_size']:
            # Keep most important memories
            self.episodic_memory = sorted(
                self.episodic_memory,
                key=lambda m: m['importance'],
                reverse=True
            )[:self.memory_params['episodic_memory_size']]
            
            # Re-sort by date
            self.episodic_memory = sorted(
                self.episodic_memory,
                key=lambda m: m['date'] if m['date'] else datetime.min
            )
            
        print(f"Built {len(self.episodic_memory)} episodic memories")
    
    def _build_semantic_memory(self, messages: List[Dict[str, Any]]) -> None:
        """Build semantic memory from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        print("Building semantic memory...")
        
        # Extract text content
        texts = [m.get('text', '') for m in messages if m.get('text')]
        
        # Extract semantic information using patterns
        self._extract_facts(texts)
        self._extract_preferences(texts)
        self._extract_opinions(texts)
        self._extract_knowledge(texts)
        
        print(f"Built semantic memory with {len(self.semantic_memory)} concepts")
    
    def _extract_facts(self, texts: List[str]) -> None:
        """Extract factual information from texts.
        
        Args:
            texts: List of text messages.
        """
        # Patterns for factual statements
        fact_patterns = [
            r'(?:I|we) (?:have|had|own|possess|got|bought|purchased) (?:a|an|the|some|my|our)? (.{3,50})',
            r'(?:I|we) (?:am|are|was|were|have been|will be) (?:at|in|on|near|by|close to) (.{3,50})',
            r'(?:I|we) (?:am|are|was|were) (?:a|an|the)? (.{3,50})',
            r'(?:my|our) (?:name|address|number|email|contact|phone) is (.{3,50})',
            r'(?:I|we) (?:live|stay|reside|work) (?:at|in|on|near|by|close to) (.{3,50})',
            r'(?:I|we) (?:work|study) (?:at|in|on|for|with) (.{3,50})'
        ]
        
        # Extract facts
        facts = []
        for text in texts:
            for pattern in fact_patterns:
                matches = re.findall(pattern, text)
                facts.extend(matches)
                
        # Clean and deduplicate facts
        cleaned_facts = []
        for fact in facts:
            fact = fact.strip()
            if len(fact) > 3 and fact not in cleaned_facts:
                cleaned_facts.append(fact)
                
        # Add to semantic memory
        for fact in cleaned_facts:
            self.semantic_memory[f"fact:{fact}"] = {
                'type': 'semantic',
                'subtype': 'fact',
                'content': fact,
                'confidence': 0.8,
                'last_accessed': datetime.now(),
                'access_count': 0,
                'keywords': extract_keywords(fact, 5)
            }
    
    def _extract_preferences(self, texts: List[str]) -> None:
        """Extract preferences from texts.
        
        Args:
            texts: List of text messages.
        """
        # Patterns for preferences
        preference_patterns = [
            r'(?:I|we) (?:like|love|enjoy|prefer|favor|fancy) (.{3,50})',
            r'(?:I|we) (?:don\'t|do not) (?:like|love|enjoy|prefer|favor|fancy) (.{3,50})',
            r'(?:I|we) (?:hate|dislike|detest|loathe|despise|can\'t stand) (.{3,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:fond of|keen on|into|partial to) (.{3,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:not fond of|not keen on|not into|not partial to) (.{3,50})',
            r'(?:My|Our) favorite (.{3,50})',
            r'(?:I|we) would (?:rather|prefer to) (.{3,50})',
            r'(?:I|we) would (?:never|not) (.{3,50})'
        ]
        
        # Extract preferences
        preferences = []
        for text in texts:
            for i, pattern in enumerate(preference_patterns):
                matches = re.findall(pattern, text)
                
                # Determine if positive or negative preference
                is_positive = i in [0, 3, 5, 6]
                
                for match in matches:
                    preferences.append((match, is_positive))
                    
        # Clean and deduplicate preferences
        cleaned_preferences = []
        for preference, is_positive in preferences:
            preference = preference.strip()
            if len(preference) > 3:
                # Check if already exists with opposite polarity
                found = False
                for i, (existing_pref, existing_pos) in enumerate(cleaned_preferences):
                    if preference == existing_pref and is_positive != existing_pos:
                        # Remove conflicting preference
                        found = True
                        cleaned_preferences.pop(i)
                        break
                        
                if not found:
                    cleaned_preferences.append((preference, is_positive))
                    
        # Add to semantic memory
        for preference, is_positive in cleaned_preferences:
            subtype = 'preference_positive' if is_positive else 'preference_negative'
            self.semantic_memory[f"{subtype}:{preference}"] = {
                'type': 'semantic',
                'subtype': subtype,
                'content': preference,
                'confidence': 0.7,
                'last_accessed': datetime.now(),
                'access_count': 0,
                'keywords': extract_keywords(preference, 5)
            }
    
    def _extract_opinions(self, texts: List[str]) -> None:
        """Extract opinions from texts.
        
        Args:
            texts: List of text messages.
        """
        # Patterns for opinions
        opinion_patterns = [
            r'(?:I|we) (?:think|believe|feel|consider) (?:that )?(.{5,100})',
            r'(?:I|we) (?:don\'t|do not) (?:think|believe|feel|consider) (?:that )?(.{5,100})',
            r'(?:In my|In our) opinion[,\s]+(.{5,100})',
            r'(?:I|we) (?:agree|disagree) (?:with|that) (.{5,100})',
            r'(?:I\'m|I am|We\'re|We are) (?:convinced|sure|certain|positive) (?:that )?(.{5,100})'
        ]
        
        # Extract opinions
        opinions = []
        for text in texts:
            for i, pattern in enumerate(opinion_patterns):
                matches = re.findall(pattern, text)
                
                # Determine if positive or negative opinion
                is_negative = i == 1 or 'disagree' in pattern
                
                for match in matches:
                    opinions.append((match, not is_negative))
                    
        # Clean and deduplicate opinions
        cleaned_opinions = []
        for opinion, is_positive in opinions:
            opinion = opinion.strip()
            if len(opinion) > 5 and not opinion.lower().startswith(('i ', 'we ', 'you ', 'they ')):
                # Check if already exists with opposite polarity
                found = False
                for i, (existing_op, existing_pos) in enumerate(cleaned_opinions):
                    if calculate_text_similarity(opinion, existing_op) > 0.8 and is_positive != existing_pos:
                        # Remove conflicting opinion
                        found = True
                        cleaned_opinions.pop(i)
                        break
                        
                if not found:
                    cleaned_opinions.append((opinion, is_positive))
                    
        # Add to semantic memory
        for opinion, is_positive in cleaned_opinions:
            subtype = 'opinion_positive' if is_positive else 'opinion_negative'
            self.semantic_memory[f"{subtype}:{opinion}"] = {
                'type': 'semantic',
                'subtype': subtype,
                'content': opinion,
                'confidence': 0.6,
                'last_accessed': datetime.now(),
                'access_count': 0,
                'keywords': extract_keywords(opinion, 5)
            }
    
    def _extract_knowledge(self, texts: List[str]) -> None:
        """Extract knowledge from texts.
        
        Args:
            texts: List of text messages.
        """
        # Patterns for knowledge
        knowledge_patterns = [
            r'(?:did you know|fun fact|interesting fact)[:\s]+(.{5,100})',
            r'(?:the|a|an) (.{3,20}) is (?:a|an|the)? (.{5,50})',
            r'(?:the|a|an) (.{3,20}) (?:are|were) (?:a|an|the)? (.{5,50})'
        ]
        
        # Extract knowledge
        knowledge = []
        for text in texts:
            for pattern in knowledge_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                if isinstance(matches, list) and matches and isinstance(matches[0], tuple):
                    # Pattern with groups
                    for match in matches:
                        if len(match) == 2:
                            knowledge.append(f"{match[0]} is {match[1]}")
                else:
                    # Pattern with single group
                    knowledge.extend(matches)
                    
        # Clean and deduplicate knowledge
        cleaned_knowledge = []
        for item in knowledge:
            item = item.strip()
            if len(item) > 5 and item not in cleaned_knowledge:
                cleaned_knowledge.append(item)
                
        # Add to semantic memory
        for item in cleaned_knowledge:
            self.semantic_memory[f"knowledge:{item}"] = {
                'type': 'semantic',
                'subtype': 'knowledge',
                'content': item,
                'confidence': 0.5,
                'last_accessed': datetime.now(),
                'access_count': 0,
                'keywords': extract_keywords(item, 5)
            }
    
    def _build_entity_memory(self, messages: List[Dict[str, Any]]) -> None:
        """Build entity memory from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        print("Building entity memory...")
        
        # Extract people entities
        self._extract_people(messages)
        
        # Extract place entities
        self._extract_places(messages)
        
        # Extract organization entities
        self._extract_organizations(messages)
        
        print(f"Built entity memory with {len(self.entity_memory)} entities")
    
    def _extract_people(self, messages: List[Dict[str, Any]]) -> None:
        """Extract people entities from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        # Get all conversation participants
        participants = set()
        for message in messages:
            chat_session = message.get('chat_session', '')
            if chat_session:
                participants.add(chat_session)
                
            if message.get('type') == 'Incoming' and message.get('sender_name'):
                participants.add(message.get('sender_name'))
                
        # Extract information about each person
        for person in participants:
            if not person:
                continue
                
            # Get messages involving this person
            person_messages = [
                m for m in messages if 
                m.get('chat_session') == person or 
                (m.get('type') == 'Incoming' and m.get('sender_name') == person)
            ]
            
            if not person_messages:
                continue
                
            # Extract basic information
            try:
                first_interaction = min(
                    datetime.strptime(m.get('message_date', ''), '%Y-%m-%d %H:%M:%S') 
                    for m in person_messages 
                    if m.get('message_date')
                )
            except (ValueError, TypeError):
                first_interaction = None
                
            try:
                last_interaction = max(
                    datetime.strptime(m.get('message_date', ''), '%Y-%m-%d %H:%M:%S') 
                    for m in person_messages 
                    if m.get('message_date')
                )
            except (ValueError, TypeError):
                last_interaction = None
                
            # Count interactions
            interaction_count = len(person_messages)
            
            # Extract topics discussed
            texts = [m.get('text', '') for m in person_messages if m.get('text')]
            all_text = ' '.join(texts)
            topics = extract_keywords(all_text, 10)
            
            # Create entity
            self.entity_memory[f"person:{person}"] = {
                'type': 'entity',
                'subtype': 'person',
                'name': person,
                'first_interaction': first_interaction,
                'last_interaction': last_interaction,
                'interaction_count': interaction_count,
                'topics': topics,
                'importance': self._calculate_entity_importance(interaction_count, first_interaction, last_interaction),
                'last_accessed': datetime.now(),
                'access_count': 0
            }
    
    def _extract_places(self, messages: List[Dict[str, Any]]) -> None:
        """Extract place entities from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        # Patterns for places
        place_patterns = [
            r'(?:at|in|on|near|by|close to|from) (?:the )?((?:[A-Z][a-z]+ )*(?:Street|Avenue|Road|Boulevard|Lane|Drive|Place|Court|Plaza|Square|Mall|Park|Building|Tower|Center|Centre|Airport|Station|Hospital|School|College|University|Library|Museum|Theater|Theatre|Stadium|Arena|Restaurant|Cafe|Bar|Pub|Club|Hotel|Motel|Inn|Resort|Beach|Mountain|Lake|River|Ocean|Sea|Island|Forest|Desert|Village|Town|City|County|State|Province|Country|Continent))',
            r'(?:at|in|on|near|by|close to|from) (?:the )?((?:[A-Z][a-z]+ )*(?:St\.|Ave\.|Rd\.|Blvd\.|Ln\.|Dr\.|Pl\.|Ct\.|Plz\.|Sq\.))',
            r'(?:at|in|on|near|by|close to|from) (?:the )?([A-Z][a-z]+ (?:Park|Building|Tower|Center|Centre|Airport|Station|Hospital|School|College|University|Library|Museum|Theater|Theatre|Stadium|Arena|Restaurant|Cafe|Bar|Pub|Club|Hotel|Motel|Inn|Resort))',
            r'(?:at|in|on|near|by|close to|from) (?:the )?([A-Z][a-z]+ (?:Street|Avenue|Road|Boulevard|Lane|Drive|Place|Court|Plaza|Square))',
            r'(?:at|in|on|near|by|close to|from) (?:the )?([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        # Extract places
        places = []
        for message in messages:
            text = message.get('text', '')
            if not text:
                continue
                
            for pattern in place_patterns:
                matches = re.findall(pattern, text)
                places.extend(matches)
                
        # Clean and deduplicate places
        cleaned_places = []
        for place in places:
            if isinstance(place, tuple):
                place = ' '.join(place)
                
            place = place.strip()
            if len(place) > 3 and place not in cleaned_places:
                cleaned_places.append(place)
                
        # Add to entity memory
        for place in cleaned_places:
            # Count mentions
            mention_count = sum(1 for p in places if p == place)
            
            # Create entity
            self.entity_memory[f"place:{place}"] = {
                'type': 'entity',
                'subtype': 'place',
                'name': place,
                'mention_count': mention_count,
                'importance': min(1.0, mention_count / 10),
                'last_accessed': datetime.now(),
                'access_count': 0
            }
    
    def _extract_organizations(self, messages: List[Dict[str, Any]]) -> None:
        """Extract organization entities from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        # Patterns for organizations
        org_patterns = [
            r'(?:at|for|with|from|to) (?:the )?((?:[A-Z][a-z]* )*(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation|Company|Co\.|Group|Agency|Association|Society|Institute|University|College|School|Hospital|Bank|Foundation|Fund|Trust|Union|League|Federation|Department|Ministry|Committee|Commission|Council|Board|Authority|Administration))',
            r'(?:at|for|with|from|to) (?:the )?([A-Z][a-z]+ (?:Inc\.|LLC|Ltd\.|Corp\.|Corporation|Company|Co\.|Group))',
            r'(?:at|for|with|from|to) (?:the )?([A-Z][A-Za-z]+ (?:University|College|School|Hospital|Bank|Foundation|Fund|Trust))',
            r'(?:at|for|with|from|to) (?:the )?([A-Z][A-Za-z]+ [A-Z][A-Za-z]+ (?:Inc\.|LLC|Ltd\.|Corp\.|Corporation|Company|Co\.|Group))'
        ]
        
        # Extract organizations
        organizations = []
        for message in messages:
            text = message.get('text', '')
            if not text:
                continue
                
            for pattern in org_patterns:
                matches = re.findall(pattern, text)
                organizations.extend(matches)
                
        # Clean and deduplicate organizations
        cleaned_orgs = []
        for org in organizations:
            if isinstance(org, tuple):
                org = ' '.join(org)
                
            org = org.strip()
            if len(org) > 3 and org not in cleaned_orgs:
                cleaned_orgs.append(org)
                
        # Add to entity memory
        for org in cleaned_orgs:
            # Count mentions
            mention_count = sum(1 for o in organizations if o == org)
            
            # Create entity
            self.entity_memory[f"organization:{org}"] = {
                'type': 'entity',
                'subtype': 'organization',
                'name': org,
                'mention_count': mention_count,
                'importance': min(1.0, mention_count / 10),
                'last_accessed': datetime.now(),
                'access_count': 0
            }
    
    def _calculate_memory_importance(self, content: List[str], participants: List[str]) -> float:
        """Calculate importance score for a memory.
        
        Args:
            content: Memory content.
            participants: Memory participants.
            
        Returns:
            Importance score (0-1).
        """
        # Base importance
        importance = 0.5
        
        # Combine content
        combined_content = ' '.join(content)
        
        # Check for emotional content
        emotional_words = [
            'love', 'hate', 'happy', 'sad', 'angry', 'excited', 'worried', 'scared',
            'anxious', 'proud', 'disappointed', 'frustrated', 'grateful', 'sorry',
            'miss', 'hope', 'wish', 'dream', 'fear', 'regret', 'enjoy', 'like',
            'dislike', 'amazing', 'terrible', 'wonderful', 'awful', 'important'
        ]
        
        emotional_count = sum(1 for word in emotional_words if word in combined_content.lower())
        importance += min(0.2, emotional_count * 0.02)
        
        # Check for question-answer patterns
        question_count = combined_content.count('?')
        importance += min(0.1, question_count * 0.02)
        
        # Check for decision-making language
        decision_words = [
            'decide', 'choice', 'choose', 'option', 'alternative', 'select',
            'pick', 'prefer', 'should', 'would', 'could', 'will', 'going to',
            'plan', 'intend', 'want', 'need', 'must', 'have to'
        ]
        
        decision_count = sum(1 for word in decision_words if word in combined_content.lower())
        importance += min(0.1, decision_count * 0.02)
        
        # Check for personal information
        personal_patterns = [
            r'\b(?:my|your|our)\s+(?:name|address|phone|email|number|birthday|age|job|work|school|family)\b',
            r'\b(?:I|we)\s+(?:live|work|study|go to|attend)\b',
            r'\b(?:I|we)\s+(?:am|are|was|were)\s+(?:born|raised|from)\b'
        ]
        
        personal_count = sum(1 for pattern in personal_patterns if re.search(pattern, combined_content, re.IGNORECASE))
        importance += min(0.1, personal_count * 0.05)
        
        return min(1.0, importance)
    
    def _calculate_entity_importance(self, interaction_count: int, first_interaction: Optional[datetime], last_interaction: Optional[datetime]) -> float:
        """Calculate importance score for an entity.
        
        Args:
            interaction_count: Number of interactions with the entity.
            first_interaction: Date of first interaction.
            last_interaction: Date of last interaction.
            
        Returns:
            Importance score (0-1).
        """
        # Base importance based on interaction count
        importance = min(0.8, interaction_count / 100)
        
        # Adjust based on recency
        if last_interaction:
            days_since_last = (datetime.now() - last_interaction).days
            recency_factor = max(0.0, 1.0 - (days_since_last / 365))
            importance += recency_factor * 0.1
            
        # Adjust based on relationship duration
        if first_interaction and last_interaction:
            relationship_days = (last_interaction - first_interaction).days
            duration_factor = min(1.0, relationship_days / 365)
            importance += duration_factor * 0.1
            
        return min(1.0, importance)
    
    def _update_memory_stats(self) -> None:
        """Update memory statistics."""
        # Count memories by type
        self.memory_stats['total_episodic_memories'] = len(self.episodic_memory)
        self.memory_stats['total_semantic_memories'] = len(self.semantic_memory)
        self.memory_stats['total_entity_memories'] = len(self.entity_memory)
        
        # Group episodic memories by recency
        recency_groups = {
            'last_day': 0,
            'last_week': 0,
            'last_month': 0,
            'last_year': 0,
            'older': 0
        }
        
        for memory in self.episodic_memory:
            if not memory['date']:
                continue
                
            days_ago = (datetime.now() - memory['date']).days
            
            if days_ago <= 1:
                recency_groups['last_day'] += 1
            elif days_ago <= 7:
                recency_groups['last_week'] += 1
            elif days_ago <= 30:
                recency_groups['last_month'] += 1
            elif days_ago <= 365:
                recency_groups['last_year'] += 1
            else:
                recency_groups['older'] += 1
                
        self.memory_stats['memory_by_recency'] = recency_groups
        
        # Group memories by importance
        importance_groups = {
            'very_high': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'very_low': 0
        }
        
        for memory in self.episodic_memory:
            importance = memory['importance']
            
            if importance >= 0.8:
                importance_groups['very_high'] += 1
            elif importance >= 0.6:
                importance_groups['high'] += 1
            elif importance >= 0.4:
                importance_groups['medium'] += 1
            elif importance >= 0.2:
                importance_groups['low'] += 1
            else:
                importance_groups['very_low'] += 1
                
        self.memory_stats['memory_by_importance'] = importance_groups
    
    def save(self) -> None:
        """Save the memory model."""
        model_path = os.path.join(self.model_dir, 'memory_model.pkl')
        save_pickle(self.__dict__, model_path)
        print(f"Memory model saved to {model_path}")
    
    def load(self) -> bool:
        """Load the memory model.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        model_path = os.path.join(self.model_dir, 'memory_model.pkl')
        
        if os.path.exists(model_path):
            try:
                data = load_pickle(model_path)
                self.__dict__.update(data)
                self.is_loaded = True
                print(f"Memory model loaded from {model_path}")
                return True
            except Exception as e:
                print(f"Error loading memory model: {e}")
                return False
        else:
            print(f"Memory model not found at {model_path}")
            return False
    
    def get_episodic_memory(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get episodic memories.
        
        Args:
            limit: Maximum number of memories to return.
            
        Returns:
            List of episodic memory dictionaries.
        """
        if limit:
            return self.episodic_memory[-limit:]
        return self.episodic_memory
    
    def get_semantic_memory(self, subtype: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get semantic memories.
        
        Args:
            subtype: Optional subtype filter.
            
        Returns:
            Dictionary of semantic memories.
        """
        if subtype:
            return {k: v for k, v in self.semantic_memory.items() if v['subtype'] == subtype}
        return self.semantic_memory
    
    def get_entity_memory(self, subtype: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get entity memories.
        
        Args:
            subtype: Optional subtype filter.
            
        Returns:
            Dictionary of entity memories.
        """
        if subtype:
            return {k: v for k, v in self.entity_memory.items() if v['subtype'] == subtype}
        return self.entity_memory
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary of memory statistics.
        """
        return self.memory_stats
    
    def search_memory(self, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for relevant items.
        
        Args:
            query: Search query.
            memory_type: Optional memory type filter ('episodic', 'semantic', 'entity').
            limit: Maximum number of results to return.
            
        Returns:
            List of memory items sorted by relevance.
        """
        query = query.lower()
        results = []
        
        # Search episodic memory
        if not memory_type or memory_type == 'episodic':
            for memory in self.episodic_memory:
                score = 0.0
                
                # Check content
                content_text = ' '.join(memory['content']).lower()
                if query in content_text:
                    score += 0.5
                    
                # Check keywords
                for keyword, count in memory['keywords']:
                    if query in keyword.lower():
                        score += 0.3 * count
                        
                # Check participants
                for participant in memory['participants']:
                    if query in participant.lower():
                        score += 0.2
                        
                # Check context
                if query in memory['context'].lower():
                    score += 0.1
                    
                if score > 0:
                    results.append({
                        'item': memory,
                        'score': score,
                        'type': 'episodic'
                    })
                    
        # Search semantic memory
        if not memory_type or memory_type == 'semantic':
            for key, memory in self.semantic_memory.items():
                score = 0.0
                
                # Check content
                content = memory['content'].lower()
                if query in content:
                    score += 0.5
                    
                # Check keywords
                for keyword, count in memory['keywords']:
                    if query in keyword.lower():
                        score += 0.3 * count
                        
                if score > 0:
                    results.append({
                        'item': memory,
                        'score': score,
                        'type': 'semantic'
                    })
                    
        # Search entity memory
        if not memory_type or memory_type == 'entity':
            for key, memory in self.entity_memory.items():
                score = 0.0
                
                # Check name
                name = memory['name'].lower()
                if query in name:
                    score += 0.8
                    
                # Check topics for people
                if memory['subtype'] == 'person' and 'topics' in memory:
                    for keyword, count in memory['topics']:
                        if query in keyword.lower():
                            score += 0.2 * count
                            
                if score > 0:
                    results.append({
                        'item': memory,
                        'score': score,
                        'type': 'entity'
                    })
                    
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Update access count and last accessed time for retrieved memories
        for result in results[:limit]:
            item = result['item']
            item['access_count'] = item.get('access_count', 0) + 1
            item['last_accessed'] = datetime.now()
            
        return results[:limit]
    
    def get_recent_memories(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent episodic memories.
        
        Args:
            days: Number of days to look back.
            limit: Maximum number of memories to return.
            
        Returns:
            List of recent episodic memories.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_memories = [
            memory for memory in self.episodic_memory
            if memory['date'] and memory['date'] >= cutoff_date
        ]
        
        # Sort by date (newest first)
        recent_memories.sort(key=lambda x: x['date'], reverse=True)
        
        # Update access count and last accessed time
        for memory in recent_memories[:limit]:
            memory['access_count'] = memory.get('access_count', 0) + 1
            memory['last_accessed'] = datetime.now()
            
        return recent_memories[:limit]
    
    def get_important_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most important episodic memories.
        
        Args:
            limit: Maximum number of memories to return.
            
        Returns:
            List of important episodic memories.
        """
        # Sort by importance
        important_memories = sorted(
            self.episodic_memory,
            key=lambda x: x['importance'],
            reverse=True
        )
        
        # Update access count and last accessed time
        for memory in important_memories[:limit]:
            memory['access_count'] = memory.get('access_count', 0) + 1
            memory['last_accessed'] = datetime.now()
            
        return important_memories[:limit]
    
    def get_memories_by_participant(self, participant: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get episodic memories involving a specific participant.
        
        Args:
            participant: Participant name.
            limit: Maximum number of memories to return.
            
        Returns:
            List of episodic memories involving the participant.
        """
        participant_memories = [
            memory for memory in self.episodic_memory
            if participant in memory['participants']
        ]
        
        # Sort by date (newest first)
        participant_memories.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
        
        # Update access count and last accessed time
        for memory in participant_memories[:limit]:
            memory['access_count'] = memory.get('access_count', 0) + 1
            memory['last_accessed'] = datetime.now()
            
        return participant_memories[:limit]
    
    def get_facts_about(self, subject: str, limit: int = 10) -> List[str]:
        """Get facts about a specific subject.
        
        Args:
            subject: Subject to get facts about.
            limit: Maximum number of facts to return.
            
        Returns:
            List of facts about the subject.
        """
        subject = subject.lower()
        facts = []
        
        # Check semantic memory for facts
        for key, memory in self.semantic_memory.items():
            if memory['subtype'] == 'fact':
                content = memory['content'].lower()
                
                if subject in content:
                    facts.append(memory['content'])
                    
                    # Update access count and last accessed time
                    memory['access_count'] = memory.get('access_count', 0) + 1
                    memory['last_accessed'] = datetime.now()
                    
        return facts[:limit]
    
    def get_preferences_about(self, subject: str, limit: int = 10) -> Dict[str, List[str]]:
        """Get preferences about a specific subject.
        
        Args:
            subject: Subject to get preferences about.
            limit: Maximum number of preferences to return.
            
        Returns:
            Dictionary of positive and negative preferences.
        """
        subject = subject.lower()
        preferences = {
            'positive': [],
            'negative': []
        }
        
        # Check semantic memory for preferences
        for key, memory in self.semantic_memory.items():
            if memory['subtype'] in ('preference_positive', 'preference_negative'):
                content = memory['content'].lower()
                
                if subject in content:
                    if memory['subtype'] == 'preference_positive':
                        preferences['positive'].append(memory['content'])
                    else:
                        preferences['negative'].append(memory['content'])
                        
                    # Update access count and last accessed time
                    memory['access_count'] = memory.get('access_count', 0) + 1
                    memory['last_accessed'] = datetime.now()
                    
        # Limit results
        preferences['positive'] = preferences['positive'][:limit]
        preferences['negative'] = preferences['negative'][:limit]
        
        return preferences
    
    def get_entity_info(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific entity.
        
        Args:
            entity_name: Name of the entity.
            
        Returns:
            Entity information or None if not found.
        """
        entity_name = entity_name.lower()
        
        # Search entity memory
        for key, entity in self.entity_memory.items():
            if entity_name in entity['name'].lower():
                # Update access count and last accessed time
                entity['access_count'] = entity.get('access_count', 0) + 1
                entity['last_accessed'] = datetime.now()
                
                return entity
                
        return None
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of the memory model.
        
        Returns:
            Dictionary containing memory summary.
        """
        return {
            'episodic_memory_count': len(self.episodic_memory),
            'semantic_memory_count': len(self.semantic_memory),
            'entity_memory_count': len(self.entity_memory),
            'memory_by_recency': self.memory_stats.get('memory_by_recency', {}),
            'memory_by_importance': self.memory_stats.get('memory_by_importance', {}),
            'recent_memories': self.get_recent_memories(7, 5),
            'important_memories': self.get_important_memories(5),
            'top_entities': sorted(
                self.entity_memory.values(),
                key=lambda x: x['importance'],
                reverse=True
            )[:5]
        }
    
    def generate_memory_description(self) -> str:
        """Generate a human-readable description of the memory model.
        
        Returns:
            Text description of the memory model.
        """
        if not self.is_loaded:
            return "Memory model not loaded."
            
        description = []
        
        # Memory overview
        description.append("# Memory Profile\n")
        
        description.append("## Memory Overview\n")
        description.append(f"- **Episodic memories**: {len(self.episodic_memory)} specific events and conversations")
        description.append(f"- **Semantic memories**: {len(self.semantic_memory)} facts, preferences, and knowledge")
        description.append(f"- **Entity memories**: {len(self.entity_memory)} people, places, and organizations")
        
        # Memory recency
        description.append("\n## Memory Recency\n")
        
        recency = self.memory_stats.get('memory_by_recency', {})
        if recency:
            description.append(f"- Last day: {recency.get('last_day', 0)} memories")
            description.append(f"- Last week: {recency.get('last_week', 0)} memories")
            description.append(f"- Last month: {recency.get('last_month', 0)} memories")
            description.append(f"- Last year: {recency.get('last_year', 0)} memories")
            description.append(f"- Older: {recency.get('older', 0)} memories")
            
        # Important memories
        description.append("\n## Important Memories\n")
        
        important_memories = self.get_important_memories(3)
        if important_memories:
            for memory in important_memories:
                date_str = memory['date'].strftime('%Y-%m-%d') if memory['date'] else 'Unknown date'
                participants_str = ', '.join(memory['participants'])
                
                description.append(f"- **{date_str}** with {participants_str}:")
                
                # Add a sample of the conversation
                sample_content = memory['content'][:2]  # First 2 messages
                for content in sample_content:
                    description.append(f"  - {content}")
                    
                if len(memory['content']) > 2:
                    description.append("  - ...")
                    
        # Key people
        description.append("\n## Key People\n")
        
        people = [e for e in self.entity_memory.values() if e['subtype'] == 'person']
        top_people = sorted(people, key=lambda x: x['importance'], reverse=True)[:5]
        
        if top_people:
            for person in top_people:
                description.append(f"- **{person['name']}**:")
                
                # Add interaction stats
                interaction_count = person.get('interaction_count', 0)
                description.append(f"  - {interaction_count} interactions")
                
                # Add first and last interaction
                first_date = person.get('first_interaction')
                last_date = person.get('last_interaction')
                
                if first_date and last_date:
                    first_str = first_date.strftime('%Y-%m-%d')
                    last_str = last_date.strftime('%Y-%m-%d')
                    description.append(f"  - First interaction: {first_str}")
                    description.append(f"  - Last interaction: {last_str}")
                    
                # Add topics
                topics = person.get('topics', [])
                if topics:
                    topic_str = ', '.join(topic for topic, _ in topics[:3])
                    description.append(f"  - Common topics: {topic_str}")
                    
        # Facts and preferences
        description.append("\n## Knowledge and Preferences\n")
        
        # Count facts and preferences
        fact_count = len([m for m in self.semantic_memory.values() if m['subtype'] == 'fact'])
        pref_pos_count = len([m for m in self.semantic_memory.values() if m['subtype'] == 'preference_positive'])
        pref_neg_count = len([m for m in self.semantic_memory.values() if m['subtype'] == 'preference_negative'])
        opinion_count = len([m for m in self.semantic_memory.values() if m['subtype'] in ('opinion_positive', 'opinion_negative')])
        
        description.append(f"- **Facts**: {fact_count} stored facts")
        description.append(f"- **Preferences**: {pref_pos_count} likes, {pref_neg_count} dislikes")
        description.append(f"- **Opinions**: {opinion_count} opinions on various topics")
        
        # Sample preferences
        pos_prefs = [m['content'] for m in self.semantic_memory.values() if m['subtype'] == 'preference_positive']
        neg_prefs = [m['content'] for m in self.semantic_memory.values() if m['subtype'] == 'preference_negative']
        
        if pos_prefs:
            description.append("\nSample likes:")
            for pref in pos_prefs[:3]:
                description.append(f"- {pref}")
                
        if neg_prefs:
            description.append("\nSample dislikes:")
            for pref in neg_prefs[:3]:
                description.append(f"- {pref}")
                
        return "\n".join(description)