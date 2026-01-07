"""Integrated cognitive model for MindMirror."""

import os
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime

from ...core.config import config_manager
from ...core.utils import save_pickle, load_pickle, ensure_dir
from .personality import PersonalityModel
from .values import ValuesModel
from .decision import DecisionModel
from .memory import MemoryModel

class CognitiveModel:
    """Integrated cognitive model combining personality, values, decision-making, and memory."""
    
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the cognitive model.
        
        Args:
            model_dir: Directory to store model data.
        """
        self.model_dir = model_dir or config_manager.get_value('mindmirror', 'data.model_dir', 'data/models')
        ensure_dir(self.model_dir)
        
        # Initialize component models
        self.personality_model = PersonalityModel(self.model_dir)
        self.values_model = ValuesModel(self.model_dir)
        self.decision_model = DecisionModel(self.model_dir)
        self.memory_model = MemoryModel(self.model_dir)
        
        # Integration parameters
        self.integration_params = {
            'personality_weight': 0.25,
            'values_weight': 0.25,
            'decision_weight': 0.25,
            'memory_weight': 0.25
        }
        
        # Model metadata
        self.metadata = {
            'created_at': datetime.now(),
            'last_updated': datetime.now(),
            'version': '1.0.0',
            'training_status': {
                'personality': False,
                'values': False,
                'decision': False,
                'memory': False
            }
        }
        
        # Loaded flag
        self.is_loaded = False
        
    def train(self, messages: List[Dict[str, Any]], user_name: Optional[str] = None) -> None:
        """Train the cognitive model on messages.
        
        Args:
            messages: List of messages to train on.
            user_name: Name of the user (to identify outgoing messages).
        """
        print("Training cognitive model...")
        
        # Train component models
        print("\nTraining personality model...")
        self.personality_model.train(messages, user_name)
        self.metadata['training_status']['personality'] = True
        
        print("\nTraining values model...")
        self.values_model.train(messages, user_name)
        self.metadata['training_status']['values'] = True
        
        print("\nTraining decision model...")
        self.decision_model.train(messages, user_name)
        self.metadata['training_status']['decision'] = True
        
        print("\nTraining memory model...")
        self.memory_model.train(messages, user_name)
        self.metadata['training_status']['memory'] = True
        
        # Update metadata
        self.metadata['last_updated'] = datetime.now()
        
        # Save the model
        self.save()
        
        self.is_loaded = True
        print("\nCognitive model training complete")
        
    def save(self) -> None:
        """Save the cognitive model."""
        # Save component models
        self.personality_model.save()
        self.values_model.save()
        self.decision_model.save()
        self.memory_model.save()
        
        # Save integration parameters and metadata
        model_path = os.path.join(self.model_dir, 'cognitive_model.pkl')
        save_pickle({
            'integration_params': self.integration_params,
            'metadata': self.metadata
        }, model_path)
        
        print(f"Cognitive model saved to {self.model_dir}")
        
    def load(self) -> bool:
        """Load the cognitive model.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        # Load component models
        personality_loaded = self.personality_model.load()
        values_loaded = self.values_model.load()
        decision_loaded = self.decision_model.load()
        memory_loaded = self.memory_model.load()
        
        # Load integration parameters and metadata
        model_path = os.path.join(self.model_dir, 'cognitive_model.pkl')
        
        if os.path.exists(model_path):
            try:
                data = load_pickle(model_path)
                self.integration_params = data.get('integration_params', self.integration_params)
                self.metadata = data.get('metadata', self.metadata)
            except Exception as e:
                print(f"Error loading cognitive model metadata: {e}")
                
        # Check if all component models were loaded
        all_loaded = personality_loaded and values_loaded and decision_loaded and memory_loaded
        
        if all_loaded:
            self.is_loaded = True
            print("Cognitive model loaded successfully")
        else:
            print("Some component models failed to load")
            
        return all_loaded
        
    def get_personality_profile(self) -> Dict[str, Any]:
        """Get personality profile.
        
        Returns:
            Dictionary containing personality profile.
        """
        if not self.personality_model.is_loaded:
            return {"error": "Personality model not loaded"}
            
        return {
            'big_five': self.personality_model.get_big_five(),
            'communication_style': self.personality_model.get_communication_style(),
            'emotion_patterns': self.personality_model.get_emotion_patterns(),
            'top_vocabulary': self.personality_model.get_top_vocabulary(20),
            'top_phrases': self.personality_model.get_top_phrases(10),
            'top_emojis': self.personality_model.get_top_emojis(10)
        }
        
    def get_values_profile(self) -> Dict[str, Any]:
        """Get values profile.
        
        Returns:
            Dictionary containing values profile.
        """
        if not self.values_model.is_loaded:
            return {"error": "Values model not loaded"}
            
        return {
            'core_values': self.values_model.get_core_values(),
            'moral_foundations': self.values_model.get_moral_foundations(),
            'belief_systems': self.values_model.get_belief_systems(),
            'top_values': self.values_model.get_top_values(5),
            'value_statements': self.values_model.get_value_statements()[:10],
            'value_conflicts': self.values_model.get_value_conflicts()
        }
        
    def get_decision_profile(self) -> Dict[str, Any]:
        """Get decision-making profile.
        
        Returns:
            Dictionary containing decision-making profile.
        """
        if not self.decision_model.is_loaded:
            return {"error": "Decision model not loaded"}
            
        return {
            'decision_style': self.decision_model.get_decision_style(),
            'decision_patterns': self.decision_model.get_decision_patterns(),
            'top_decision_topics': self.decision_model.get_top_decision_topics(5),
            'recent_decisions': self.decision_model.get_decision_history(5),
            'preferences': {
                'likes': self.decision_model.get_top_preferences('likes', 5),
                'dislikes': self.decision_model.get_top_preferences('dislikes', 5)
            }
        }
        
    def get_memory_profile(self) -> Dict[str, Any]:
        """Get memory profile.
        
        Returns:
            Dictionary containing memory profile.
        """
        if not self.memory_model.is_loaded:
            return {"error": "Memory model not loaded"}
            
        return {
            'memory_stats': self.memory_model.get_memory_stats(),
            'recent_memories': self.memory_model.get_recent_memories(7, 5),
            'important_memories': self.memory_model.get_important_memories(5),
            'top_entities': sorted(
                self.memory_model.get_entity_memory().values(),
                key=lambda x: x['importance'],
                reverse=True
            )[:5]
        }
        
    def get_cognitive_profile(self) -> Dict[str, Any]:
        """Get complete cognitive profile.
        
        Returns:
            Dictionary containing complete cognitive profile.
        """
        return {
            'personality': self.get_personality_profile(),
            'values': self.get_values_profile(),
            'decision': self.get_decision_profile(),
            'memory': self.get_memory_profile(),
            'metadata': self.metadata
        }
        
    def predict_decision(self, options: List[str], context: str = '') -> Dict[str, Any]:
        """Predict a decision based on the cognitive model.
        
        Args:
            options: List of decision options.
            context: Decision context.
            
        Returns:
            Dictionary with predicted decision and confidence.
        """
        if not self.is_loaded:
            return {'decision': None, 'confidence': 0.0, 'reasoning': 'Model not loaded'}
            
        # Get base decision prediction from decision model
        base_prediction = self.decision_model.predict_decision(options, context)
        
        # If no valid prediction, return as is
        if not base_prediction['decision']:
            return base_prediction
            
        # Adjust based on values
        adjusted_prediction = self._adjust_decision_with_values(base_prediction, options)
        
        # Adjust based on memory
        final_prediction = self._adjust_decision_with_memory(adjusted_prediction, options, context)
        
        return final_prediction
        
    def _adjust_decision_with_values(self, prediction: Dict[str, Any], options: List[str]) -> Dict[str, Any]:
        """Adjust decision prediction based on values.
        
        Args:
            prediction: Base prediction from decision model.
            options: List of decision options.
            
        Returns:
            Adjusted prediction.
        """
        if not self.values_model.is_loaded:
            return prediction
            
        decision = prediction['decision']
        confidence = prediction['confidence']
        all_scores = prediction.get('all_scores', {})
        
        # Get top values
        top_values = self.values_model.get_top_values(3)
        
        # Check if decision aligns with top values
        value_alignment = 0.0
        value_reasoning = []
        
        for value_name, value_score in top_values:
            # Check if decision contains words related to this value
            value_keywords = self.values_model.value_lexicon.get(value_name, [])
            
            for keyword in value_keywords:
                if keyword in decision.lower():
                    value_alignment += value_score * 0.1
                    value_reasoning.append(f"Aligns with {value_name} value")
                    break
                    
        # Adjust confidence based on value alignment
        adjusted_confidence = confidence + value_alignment
        
        # Ensure confidence is in valid range
        adjusted_confidence = min(1.0, max(0.0, adjusted_confidence))
        
        # Update reasoning
        reasoning = prediction['reasoning']
        if value_reasoning:
            reasoning += " " + " ".join(value_reasoning)
            
        return {
            'decision': decision,
            'confidence': adjusted_confidence,
            'reasoning': reasoning,
            'all_scores': all_scores
        }
        
    def _adjust_decision_with_memory(self, prediction: Dict[str, Any], options: List[str], context: str) -> Dict[str, Any]:
        """Adjust decision prediction based on memory.
        
        Args:
            prediction: Prediction adjusted with values.
            options: List of decision options.
            context: Decision context.
            
        Returns:
            Final adjusted prediction.
        """
        if not self.memory_model.is_loaded:
            return prediction
            
        decision = prediction['decision']
        confidence = prediction['confidence']
        all_scores = prediction.get('all_scores', {})
        
        # Search memory for relevant information
        memory_results = self.memory_model.search_memory(decision, limit=5)
        
        # Check if there are relevant memories
        memory_alignment = 0.0
        memory_reasoning = []
        
        for result in memory_results:
            item = result['item']
            score = result['score']
            
            # If it's a positive preference that matches the decision
            if item.get('subtype') == 'preference_positive' and item.get('content', '').lower() in decision.lower():
                memory_alignment += 0.1
                memory_reasoning.append(f"Matches previous preference for {item['content']}")
                
            # If it's a negative preference that matches the decision
            elif item.get('subtype') == 'preference_negative' and item.get('content', '').lower() in decision.lower():
                memory_alignment -= 0.1
                memory_reasoning.append(f"Conflicts with previous dislike of {item['content']}")
                
            # If it's an episodic memory with similar context
            elif item.get('type') == 'episodic' and context:
                content_text = ' '.join(item.get('content', []))
                if context.lower() in content_text.lower():
                    memory_alignment += 0.05
                    memory_reasoning.append("Similar to a previous situation")
                    
        # Adjust confidence based on memory alignment
        adjusted_confidence = confidence + memory_alignment
        
        # Ensure confidence is in valid range
        adjusted_confidence = min(1.0, max(0.0, adjusted_confidence))
        
        # Update reasoning
        reasoning = prediction['reasoning']
        if memory_reasoning:
            reasoning += " " + " ".join(memory_reasoning)
            
        return {
            'decision': decision,
            'confidence': adjusted_confidence,
            'reasoning': reasoning,
            'all_scores': all_scores
        }
        
    def search_memory(self, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for relevant items.
        
        Args:
            query: Search query.
            memory_type: Optional memory type filter ('episodic', 'semantic', 'entity').
            limit: Maximum number of results to return.
            
        Returns:
            List of memory items sorted by relevance.
        """
        if not self.memory_model.is_loaded:
            return []
            
        return self.memory_model.search_memory(query, memory_type, limit)
        
    def get_entity_info(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific entity.
        
        Args:
            entity_name: Name of the entity.
            
        Returns:
            Entity information or None if not found.
        """
        if not self.memory_model.is_loaded:
            return None
            
        return self.memory_model.get_entity_info(entity_name)
        
    def get_facts_about(self, subject: str, limit: int = 10) -> List[str]:
        """Get facts about a specific subject.
        
        Args:
            subject: Subject to get facts about.
            limit: Maximum number of facts to return.
            
        Returns:
            List of facts about the subject.
        """
        if not self.memory_model.is_loaded:
            return []
            
        return self.memory_model.get_facts_about(subject, limit)
        
    def get_preferences_about(self, subject: str, limit: int = 10) -> Dict[str, List[str]]:
        """Get preferences about a specific subject.
        
        Args:
            subject: Subject to get preferences about.
            limit: Maximum number of preferences to return.
            
        Returns:
            Dictionary of positive and negative preferences.
        """
        if not self.memory_model.is_loaded:
            return {'positive': [], 'negative': []}
            
        return self.memory_model.get_preferences_about(subject, limit)
        
    def generate_cognitive_description(self) -> str:
        """Generate a human-readable description of the cognitive model.
        
        Returns:
            Text description of the cognitive model.
        """
        if not self.is_loaded:
            return "Cognitive model not loaded."
            
        description = []
        
        # Add personality description
        description.append("# Cognitive Profile\n")
        description.append(self.personality_model.generate_personality_description())
        
        # Add values description
        description.append("\n" + self.values_model.generate_values_description())
        
        # Add decision description
        description.append("\n" + self.decision_model.generate_decision_description())
        
        # Add memory description
        description.append("\n" + self.memory_model.generate_memory_description())
        
        return "\n".join(description)
        
    def export_profile_json(self, filepath: str) -> None:
        """Export cognitive profile to JSON file.
        
        Args:
            filepath: Path to save the JSON file.
        """
        profile = self.get_cognitive_profile()
        
        # Convert datetime objects to strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
            
        with open(filepath, 'w') as f:
            json.dump(profile, f, default=convert_datetime, indent=2)
            
        print(f"Cognitive profile exported to {filepath}")