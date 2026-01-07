"""Values modeling for MindMirror."""

import os
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import re
from collections import Counter, defaultdict
import json

from ...core.config import config_manager
from ...core.utils import normalize_text, save_pickle, load_pickle, ensure_dir

class ValuesModel:
    """Models core values, beliefs, and moral foundations."""
    
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the values model.
        
        Args:
            model_dir: Directory to store model data.
        """
        self.model_dir = model_dir or config_manager.get_value('mindmirror', 'data.model_dir', 'data/models')
        ensure_dir(self.model_dir)
        
        # Core values
        self.core_values = {
            'achievement': 0.0,
            'benevolence': 0.0,
            'conformity': 0.0,
            'hedonism': 0.0,
            'power': 0.0,
            'security': 0.0,
            'self_direction': 0.0,
            'stimulation': 0.0,
            'tradition': 0.0,
            'universalism': 0.0
        }
        
        # Moral foundations
        self.moral_foundations = {
            'care': 0.0,
            'fairness': 0.0,
            'loyalty': 0.0,
            'authority': 0.0,
            'sanctity': 0.0,
            'liberty': 0.0
        }
        
        # Belief systems
        self.belief_systems = {
            'political': {},
            'religious': {},
            'philosophical': {}
        }
        
        # Value-related statements
        self.value_statements = []
        
        # Value conflicts
        self.value_conflicts = []
        
        # Loaded flag
        self.is_loaded = False
        
        # Value lexicons
        self._initialize_lexicons()
        
    def _initialize_lexicons(self) -> None:
        """Initialize lexicons for value detection."""
        # Core values lexicon
        self.value_lexicon = {
            'achievement': [
                'success', 'accomplish', 'achieve', 'win', 'excel', 'perform',
                'goal', 'ambition', 'progress', 'advance', 'improve', 'grow',
                'develop', 'skill', 'competent', 'capable', 'effective', 'efficient',
                'productive', 'result', 'outcome', 'complete', 'finish', 'graduate',
                'promotion', 'award', 'recognition', 'praise', 'proud', 'satisfaction'
            ],
            'benevolence': [
                'help', 'care', 'support', 'assist', 'aid', 'benefit', 'welfare',
                'kind', 'generous', 'giving', 'charity', 'donate', 'volunteer',
                'compassion', 'empathy', 'sympathy', 'concern', 'considerate',
                'thoughtful', 'selfless', 'altruistic', 'service', 'contribute'
            ],
            'conformity': [
                'follow', 'obey', 'comply', 'adhere', 'respect', 'rule', 'norm',
                'standard', 'convention', 'tradition', 'proper', 'appropriate',
                'correct', 'right', 'acceptable', 'expected', 'should', 'must',
                'obligation', 'duty', 'responsibility', 'discipline', 'order'
            ],
            'hedonism': [
                'enjoy', 'pleasure', 'fun', 'excitement', 'thrill', 'delight',
                'happy', 'joy', 'satisfy', 'indulge', 'treat', 'luxury', 'comfort',
                'relax', 'leisure', 'entertainment', 'party', 'celebrate', 'play',
                'vacation', 'holiday', 'weekend', 'good time', 'experience'
            ],
            'power': [
                'control', 'influence', 'lead', 'direct', 'manage', 'authority',
                'command', 'dominate', 'power', 'strength', 'force', 'might',
                'status', 'position', 'rank', 'prestige', 'reputation', 'respect',
                'admire', 'wealth', 'rich', 'money', 'resource', 'asset', 'property'
            ],
            'security': [
                'safe', 'secure', 'protect', 'defend', 'guard', 'shield', 'shelter',
                'stability', 'steady', 'reliable', 'dependable', 'consistent',
                'predictable', 'certain', 'sure', 'confident', 'trust', 'health',
                'well-being', 'insurance', 'prevention', 'caution', 'careful'
            ],
            'self_direction': [
                'choose', 'decide', 'determine', 'freedom', 'liberty', 'independence',
                'autonomy', 'self-reliance', 'self-sufficient', 'individual', 'unique',
                'original', 'creative', 'innovative', 'explore', 'discover', 'learn',
                'understand', 'think', 'reason', 'logic', 'analyze', 'evaluate'
            ],
            'stimulation': [
                'excite', 'thrill', 'adventure', 'risk', 'challenge', 'dare',
                'new', 'novel', 'variety', 'change', 'different', 'diverse',
                'experience', 'explore', 'discover', 'travel', 'journey', 'active',
                'energetic', 'dynamic', 'spontaneous', 'impulsive', 'surprise'
            ],
            'tradition': [
                'tradition', 'custom', 'ritual', 'ceremony', 'heritage', 'legacy',
                'history', 'ancestor', 'elder', 'respect', 'honor', 'reverence',
                'sacred', 'holy', 'spiritual', 'religious', 'faith', 'belief',
                'culture', 'identity', 'roots', 'origin', 'belong', 'community'
            ],
            'universalism': [
                'equality', 'fairness', 'justice', 'right', 'human', 'dignity',
                'respect', 'tolerance', 'accept', 'diversity', 'inclusion', 'peace',
                'harmony', 'unity', 'cooperation', 'collaborate', 'environment',
                'nature', 'earth', 'planet', 'sustainable', 'preserve', 'protect'
            ]
        }
        
        # Moral foundations lexicon
        self.moral_lexicon = {
            'care': [
                'care', 'harm', 'suffer', 'protect', 'safe', 'defend', 'hurt',
                'cruel', 'kind', 'compassion', 'empathy', 'sympathy', 'help',
                'support', 'nurture', 'comfort', 'pain', 'distress', 'vulnerable',
                'abuse', 'mistreat', 'neglect', 'abandon', 'love', 'cherish'
            ],
            'fairness': [
                'fair', 'equal', 'justice', 'right', 'deserve', 'discriminate',
                'bias', 'prejudice', 'privilege', 'disadvantage', 'opportunity',
                'chance', 'treatment', 'unfair', 'unjust', 'equitable', 'impartial',
                'honest', 'cheat', 'fraud', 'corrupt', 'integrity', 'reciprocity'
            ],
            'loyalty': [
                'loyal', 'faithful', 'betray', 'traitor', 'treason', 'patriot',
                'country', 'nation', 'flag', 'team', 'group', 'family', 'friend',
                'community', 'solidarity', 'unity', 'together', 'belong', 'member',
                'duty', 'obligation', 'commitment', 'dedicated', 'devoted', 'trust'
            ],
            'authority': [
                'authority', 'respect', 'obey', 'comply', 'follow', 'lead',
                'command', 'order', 'control', 'power', 'superior', 'inferior',
                'hierarchy', 'rank', 'status', 'position', 'tradition', 'elder',
                'parent', 'teacher', 'boss', 'expert', 'official', 'government'
            ],
            'sanctity': [
                'pure', 'sacred', 'clean', 'dirty', 'disgust', 'gross', 'disease',
                'sick', 'health', 'wholesome', 'natural', 'unnatural', 'holy',
                'divine', 'spiritual', 'religious', 'sin', 'virtue', 'vice',
                'moral', 'immoral', 'decent', 'indecent', 'obscene', 'modest'
            ],
            'liberty': [
                'free', 'freedom', 'liberty', 'independent', 'autonomy', 'choice',
                'choose', 'decide', 'oppress', 'tyranny', 'dictator', 'control',
                'restrict', 'limit', 'constrain', 'force', 'coerce', 'compel',
                'rights', 'entitle', 'sovereign', 'self-govern', 'emancipate'
            ]
        }
        
        # Belief system indicators
        self.belief_indicators = {
            'political': {
                'liberal': [
                    'liberal', 'progressive', 'democrat', 'left', 'socialism',
                    'equality', 'diversity', 'inclusion', 'social justice',
                    'welfare', 'regulation', 'environment', 'climate change',
                    'healthcare', 'education', 'workers rights', 'union',
                    'minimum wage', 'tax the rich', 'reproductive rights'
                ],
                'conservative': [
                    'conservative', 'republican', 'right', 'tradition', 'family values',
                    'free market', 'capitalism', 'small government', 'deregulation',
                    'tax cuts', 'fiscal responsibility', 'military', 'law and order',
                    'religious freedom', 'second amendment', 'pro-life', 'patriot'
                ],
                'libertarian': [
                    'libertarian', 'freedom', 'liberty', 'individual rights',
                    'small government', 'free market', 'deregulation', 'privacy',
                    'civil liberties', 'non-intervention', 'voluntary', 'consent'
                ],
                'socialist': [
                    'socialist', 'communism', 'marxist', 'collective', 'workers',
                    'labor', 'class struggle', 'inequality', 'capitalism', 'bourgeois',
                    'proletariat', 'means of production', 'exploitation', 'revolution'
                ],
                'centrist': [
                    'moderate', 'centrist', 'middle', 'bipartisan', 'compromise',
                    'pragmatic', 'practical', 'reasonable', 'balanced', 'both sides'
                ]
            },
            'religious': {
                'christian': [
                    'god', 'jesus', 'christ', 'bible', 'scripture', 'church', 'pray',
                    'faith', 'sin', 'salvation', 'heaven', 'hell', 'cross', 'worship',
                    'holy spirit', 'pastor', 'priest', 'sermon', 'baptism', 'communion'
                ],
                'jewish': [
                    'judaism', 'jewish', 'torah', 'rabbi', 'synagogue', 'hebrew',
                    'kosher', 'sabbath', 'shabbat', 'passover', 'hanukkah', 'israel',
                    'mitzvah', 'talmud', 'yom kippur', 'rosh hashanah', 'menorah'
                ],
                'muslim': [
                    'islam', 'muslim', 'quran', 'allah', 'muhammad', 'mosque', 'imam',
                    'ramadan', 'eid', 'hajj', 'prayer', 'halal', 'salat', 'zakat',
                    'shahada', 'mecca', 'medina', 'jihad', 'ummah', 'sunnah'
                ],
                'buddhist': [
                    'buddha', 'buddhism', 'meditation', 'enlightenment', 'nirvana',
                    'dharma', 'karma', 'reincarnation', 'mindfulness', 'zen',
                    'suffering', 'attachment', 'temple', 'monk', 'sangha'
                ],
                'hindu': [
                    'hinduism', 'brahman', 'atman', 'karma', 'dharma', 'reincarnation',
                    'yoga', 'meditation', 'temple', 'puja', 'mantra', 'guru', 'om',
                    'vishnu', 'shiva', 'krishna', 'ganesha', 'diwali', 'holi'
                ],
                'atheist': [
                    'atheist', 'atheism', 'secular', 'rationalist', 'skeptic',
                    'no god', 'not religious', 'science', 'evidence', 'reason',
                    'logic', 'natural', 'material', 'physical', 'empirical'
                ],
                'agnostic': [
                    'agnostic', 'uncertain', 'doubt', 'question', 'maybe',
                    'not sure', 'don\'t know', 'possible', 'unknowable'
                ],
                'spiritual': [
                    'spiritual', 'universe', 'energy', 'consciousness', 'soul',
                    'spirit', 'divine', 'sacred', 'higher power', 'metaphysical',
                    'transcendent', 'mystical', 'cosmic', 'holistic', 'intuition'
                ]
            },
            'philosophical': {
                'existentialist': [
                    'existence', 'meaning', 'purpose', 'absurd', 'freedom', 'choice',
                    'responsibility', 'authentic', 'anxiety', 'despair', 'nothingness',
                    'being', 'essence', 'subjective', 'individual', 'nietzsche', 'sartre'
                ],
                'utilitarian': [
                    'utility', 'happiness', 'pleasure', 'pain', 'greatest good',
                    'consequences', 'outcome', 'result', 'benefit', 'harm',
                    'maximize', 'optimize', 'efficient', 'bentham', 'mill'
                ],
                'pragmatist': [
                    'practical', 'useful', 'workable', 'effective', 'results',
                    'experience', 'experiment', 'test', 'try', 'adapt', 'change',
                    'improve', 'problem-solving', 'dewey', 'james', 'peirce'
                ],
                'stoic': [
                    'stoic', 'virtue', 'wisdom', 'courage', 'justice', 'temperance',
                    'acceptance', 'fate', 'nature', 'reason', 'emotion', 'control',
                    'discipline', 'endurance', 'resilience', 'marcus aurelius'
                ],
                'nihilist': [
                    'nihilism', 'meaningless', 'pointless', 'nothing matters',
                    'no purpose', 'no value', 'no truth', 'void', 'empty', 'futile',
                    'absurd', 'chaos', 'random', 'arbitrary', 'nietzsche'
                ],
                'humanist': [
                    'humanism', 'human', 'reason', 'science', 'progress', 'ethics',
                    'morality', 'dignity', 'rights', 'freedom', 'equality', 'secular',
                    'rational', 'enlightenment', 'knowledge', 'education', 'flourishing'
                ]
            }
        }
        
    def train(self, messages: List[Dict[str, Any]], user_name: Optional[str] = None) -> None:
        """Train the values model on messages.
        
        Args:
            messages: List of messages to train on.
            user_name: Name of the user (to identify outgoing messages).
        """
        print("Training values model...")
        
        # Filter to outgoing messages if user_name is provided
        if user_name:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing' or m.get('sender_name') == user_name]
        else:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing']
        
        print(f"Training on {len(outgoing_messages)} outgoing messages")
        
        # Extract text content
        texts = [m.get('text', '') for m in outgoing_messages if m.get('text')]
        
        # Analyze core values
        self._analyze_core_values(texts)
        
        # Analyze moral foundations
        self._analyze_moral_foundations(texts)
        
        # Analyze belief systems
        self._analyze_belief_systems(texts)
        
        # Extract value statements
        self._extract_value_statements(texts)
        
        # Identify value conflicts
        self._identify_value_conflicts()
        
        # Save the model
        self.save()
        
        self.is_loaded = True
        print("Values model training complete")
        
    def _analyze_core_values(self, texts: List[str]) -> None:
        """Analyze core values from texts.
        
        Args:
            texts: List of text messages.
        """
        if not texts:
            return
            
        # Initialize value scores
        value_scores = {value: 0 for value in self.core_values}
        
        # Count value-related words
        for text in texts:
            text_lower = text.lower()
            
            for value, keywords in self.value_lexicon.items():
                for keyword in keywords:
                    # Count occurrences of the keyword
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                    value_scores[value] += count
                    
        # Normalize scores
        total_score = sum(value_scores.values())
        if total_score > 0:
            self.core_values = {k: v / total_score for k, v in value_scores.items()}
            
        # Look for explicit value statements
        value_statement_patterns = [
            r'I value (\w+)',
            r'I believe in (\w+)',
            r'(\w+) is important to me',
            r'I care about (\w+)',
            r'I prioritize (\w+)',
            r'I appreciate (\w+)',
            r'I respect (\w+)',
            r'I admire (\w+)',
            r'I stand for (\w+)',
            r'I support (\w+)'
        ]
        
        for text in texts:
            text_lower = text.lower()
            
            for pattern in value_statement_patterns:
                matches = re.findall(pattern, text_lower)
                
                for match in matches:
                    # Check which value category the match belongs to
                    for value, keywords in self.value_lexicon.items():
                        if match in keywords or any(keyword in match for keyword in keywords):
                            # Boost this value
                            self.core_values[value] += 0.1
                            
        # Normalize again
        total = sum(self.core_values.values())
        if total > 0:
            self.core_values = {k: v / total for k, v in self.core_values.items()}
    
    def _analyze_moral_foundations(self, texts: List[str]) -> None:
        """Analyze moral foundations from texts.
        
        Args:
            texts: List of text messages.
        """
        if not texts:
            return
            
        # Initialize foundation scores
        foundation_scores = {foundation: 0 for foundation in self.moral_foundations}
        
        # Count foundation-related words
        for text in texts:
            text_lower = text.lower()
            
            for foundation, keywords in self.moral_lexicon.items():
                for keyword in keywords:
                    # Count occurrences of the keyword
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                    foundation_scores[foundation] += count
                    
        # Normalize scores
        total_score = sum(foundation_scores.values())
        if total_score > 0:
            self.moral_foundations = {k: v / total_score for k, v in foundation_scores.items()}
    
    def _analyze_belief_systems(self, texts: List[str]) -> None:
        """Analyze belief systems from texts.
        
        Args:
            texts: List of text messages.
        """
        if not texts:
            return
            
        # Initialize belief system scores
        belief_scores = {
            'political': defaultdict(int),
            'religious': defaultdict(int),
            'philosophical': defaultdict(int)
        }
        
        # Count belief-related words
        for text in texts:
            text_lower = text.lower()
            
            for system_type, belief_systems in self.belief_indicators.items():
                for belief, keywords in belief_systems.items():
                    for keyword in keywords:
                        # Count occurrences of the keyword
                        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                        belief_scores[system_type][belief] += count
                        
        # Normalize scores for each belief system type
        for system_type, scores in belief_scores.items():
            total_score = sum(scores.values())
            if total_score > 0:
                self.belief_systems[system_type] = {k: v / total_score for k, v in scores.items()}
    
    def _extract_value_statements(self, texts: List[str]) -> None:
        """Extract explicit value statements from texts.
        
        Args:
            texts: List of text messages.
        """
        # Patterns for value statements
        value_patterns = [
            r'I (?:think|believe|feel) (?:that )?(.{10,100})',
            r'I value (.{5,50})',
            r'I care about (.{5,50})',
            r'I support (.{5,50})',
            r'I stand for (.{5,50})',
            r'I am against (.{5,50})',
            r'I oppose (.{5,50})',
            r'I don\'t believe in (.{5,50})',
            r'I disagree with (.{5,50})',
            r'I agree with (.{5,50})',
            r'It\'s important to (.{5,50})',
            r'We should (.{5,50})',
            r'People should (.{5,50})',
            r'Everyone should (.{5,50})',
            r'Nobody should (.{5,50})',
            r'I wish (.{5,50})',
            r'I hope (.{5,50})'
        ]
        
        # Extract statements
        statements = []
        for text in texts:
            for pattern in value_patterns:
                matches = re.findall(pattern, text)
                statements.extend(matches)
                
        # Filter and clean statements
        filtered_statements = []
        for statement in statements:
            # Clean the statement
            statement = statement.strip()
            
            # Skip short statements
            if len(statement) < 10:
                continue
                
            # Skip statements that are just common phrases
            if statement.lower() in ['i don\'t know', 'i\'m not sure', 'i can\'t remember']:
                continue
                
            # Add the statement
            filtered_statements.append(statement)
            
        # Remove duplicates while preserving order
        seen = set()
        self.value_statements = [s for s in filtered_statements if not (s in seen or seen.add(s))]
    
    def _identify_value_conflicts(self) -> None:
        """Identify potential value conflicts."""
        # Define potentially conflicting value pairs
        conflicting_pairs = [
            ('self_direction', 'conformity'),
            ('self_direction', 'tradition'),
            ('stimulation', 'security'),
            ('hedonism', 'conformity'),
            ('achievement', 'benevolence'),
            ('power', 'universalism'),
            ('power', 'benevolence')
        ]
        
        # Check for conflicts
        conflicts = []
        for value1, value2 in conflicting_pairs:
            # If both values are high (above 0.4), there might be a conflict
            if self.core_values[value1] > 0.4 and self.core_values[value2] > 0.4:
                conflicts.append({
                    'values': [value1, value2],
                    'strength': self.core_values[value1] * self.core_values[value2],
                    'description': f"Potential conflict between {value1} and {value2}"
                })
                
        # Sort conflicts by strength
        self.value_conflicts = sorted(conflicts, key=lambda x: x['strength'], reverse=True)
    
    def save(self) -> None:
        """Save the values model."""
        model_path = os.path.join(self.model_dir, 'values_model.pkl')
        save_pickle(self.__dict__, model_path)
        print(f"Values model saved to {model_path}")
    
    def load(self) -> bool:
        """Load the values model.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        model_path = os.path.join(self.model_dir, 'values_model.pkl')
        
        if os.path.exists(model_path):
            try:
                data = load_pickle(model_path)
                self.__dict__.update(data)
                self.is_loaded = True
                print(f"Values model loaded from {model_path}")
                return True
            except Exception as e:
                print(f"Error loading values model: {e}")
                return False
        else:
            print(f"Values model not found at {model_path}")
            return False
    
    def get_core_values(self) -> Dict[str, float]:
        """Get core values.
        
        Returns:
            Dictionary of core values.
        """
        return self.core_values
    
    def get_moral_foundations(self) -> Dict[str, float]:
        """Get moral foundations.
        
        Returns:
            Dictionary of moral foundations.
        """
        return self.moral_foundations
    
    def get_belief_systems(self) -> Dict[str, Dict[str, float]]:
        """Get belief systems.
        
        Returns:
            Dictionary of belief systems.
        """
        return self.belief_systems
    
    def get_value_statements(self) -> List[str]:
        """Get value statements.
        
        Returns:
            List of value statements.
        """
        return self.value_statements
    
    def get_value_conflicts(self) -> List[Dict[str, Any]]:
        """Get value conflicts.
        
        Returns:
            List of value conflicts.
        """
        return self.value_conflicts
    
    def get_top_values(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get top core values.
        
        Args:
            top_n: Number of top values to return.
            
        Returns:
            List of (value, score) tuples.
        """
        return sorted(self.core_values.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_top_moral_foundations(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get top moral foundations.
        
        Args:
            top_n: Number of top foundations to return.
            
        Returns:
            List of (foundation, score) tuples.
        """
        return sorted(self.moral_foundations.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_dominant_beliefs(self) -> Dict[str, str]:
        """Get dominant beliefs for each belief system type.
        
        Returns:
            Dictionary mapping belief system types to dominant beliefs.
        """
        dominant_beliefs = {}
        
        for system_type, beliefs in self.belief_systems.items():
            if beliefs:
                dominant_belief = max(beliefs.items(), key=lambda x: x[1])
                # Only include if score is significant
                if dominant_belief[1] > 0.3:
                    dominant_beliefs[system_type] = dominant_belief[0]
                    
        return dominant_beliefs
    
    def get_values_summary(self) -> Dict[str, Any]:
        """Get a summary of the values model.
        
        Returns:
            Dictionary containing values summary.
        """
        return {
            'core_values': self.get_top_values(5),
            'moral_foundations': self.get_top_moral_foundations(3),
            'dominant_beliefs': self.get_dominant_beliefs(),
            'value_statements': self.value_statements[:5] if self.value_statements else [],
            'value_conflicts': self.value_conflicts[:3] if self.value_conflicts else []
        }
    
    def generate_values_description(self) -> str:
        """Generate a human-readable description of the values.
        
        Returns:
            Text description of the values.
        """
        if not self.is_loaded:
            return "Values model not loaded."
            
        description = []
        
        # Core values
        description.append("# Values Profile\n")
        
        description.append("## Core Values\n")
        
        # Sort values by score
        sorted_values = sorted(self.core_values.items(), key=lambda x: x[1], reverse=True)
        
        # Describe top values
        for value, score in sorted_values[:3]:
            if score > 0.1:  # Only include significant values
                description.append(f"- **{value.capitalize()}**: {score:.2f}")
                
                # Add description based on the value
                if value == 'achievement':
                    description.append("  - Values success, accomplishment, and setting and achieving goals")
                elif value == 'benevolence':
                    description.append("  - Values helping others, kindness, and caring for people's welfare")
                elif value == 'conformity':
                    description.append("  - Values following rules, meeting expectations, and social norms")
                elif value == 'hedonism':
                    description.append("  - Values enjoyment, pleasure, and having a good time")
                elif value == 'power':
                    description.append("  - Values influence, leadership, and social status")
                elif value == 'security':
                    description.append("  - Values safety, stability, and avoiding risk")
                elif value == 'self_direction':
                    description.append("  - Values independence, freedom of choice, and creativity")
                elif value == 'stimulation':
                    description.append("  - Values excitement, novelty, and challenges")
                elif value == 'tradition':
                    description.append("  - Values cultural customs, respect for tradition, and established practices")
                elif value == 'universalism':
                    description.append("  - Values equality, justice, and concern for all people and nature")
                
        # Moral foundations
        description.append("\n## Moral Foundations\n")
        
        # Sort foundations by score
        sorted_foundations = sorted(self.moral_foundations.items(), key=lambda x: x[1], reverse=True)
        
        # Describe top foundations
        for foundation, score in sorted_foundations[:3]:
            if score > 0.1:  # Only include significant foundations
                description.append(f"- **{foundation.capitalize()}**: {score:.2f}")
                
                # Add description based on the foundation
                if foundation == 'care':
                    description.append("  - Concerned with caring for others and preventing harm")
                elif foundation == 'fairness':
                    description.append("  - Concerned with fairness, justice, and equality")
                elif foundation == 'loyalty':
                    description.append("  - Concerned with loyalty to group, family, or nation")
                elif foundation == 'authority':
                    description.append("  - Concerned with respect for authority and tradition")
                elif foundation == 'sanctity':
                    description.append("  - Concerned with purity, sanctity, and avoiding disgust")
                elif foundation == 'liberty':
                    description.append("  - Concerned with freedom from oppression and coercion")
                
        # Belief systems
        description.append("\n## Belief Systems\n")
        
        # Get dominant beliefs
        dominant_beliefs = self.get_dominant_beliefs()
        
        for system_type, belief in dominant_beliefs.items():
            description.append(f"- **{system_type.capitalize()}**: {belief}")
            
        # Value statements
        if self.value_statements:
            description.append("\n## Value Statements\n")
            
            for statement in self.value_statements[:5]:
                description.append(f"- &quot;{statement}&quot;")
                
        # Value conflicts
        if self.value_conflicts:
            description.append("\n## Potential Value Conflicts\n")
            
            for conflict in self.value_conflicts[:3]:
                description.append(f"- {conflict['description']}")
                
        return "\n".join(description)