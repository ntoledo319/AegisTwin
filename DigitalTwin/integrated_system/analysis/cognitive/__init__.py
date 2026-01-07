"""
Cognitive analysis package.

This package provides cognitive analysis capabilities for the integrated system,
including personality analysis, values analysis, decision analysis, and memory analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from .personality import PersonalityAnalyzer
from .values import ValuesAnalyzer
from .decision import DecisionAnalyzer
from .memory import MemoryAnalyzer

logger = logging.getLogger(__name__)

class CognitiveAnalyzer:
    """Main cognitive analyzer."""
    
    def __init__(self):
        """Initialize the cognitive analyzer."""
        self.personality_analyzer = PersonalityAnalyzer()
        self.values_analyzer = ValuesAnalyzer()
        self.decision_analyzer = DecisionAnalyzer()
        self.memory_analyzer = MemoryAnalyzer()
        self.analysis_results = {}
    
    async def analyze(self, data: Any, communication_results: Optional[Dict[str, Any]] = None, 
                     advanced_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze data using cognitive techniques.
        
        Args:
            data: Data to analyze
            communication_results: Results from communication analysis (optional)
            advanced_results: Results from advanced analysis (optional)
            
        Returns:
            Dictionary of cognitive analysis results
        """
        logger.info("Starting cognitive analysis")
        
        # Extract messages from data
        messages = self._extract_messages(data)
        
        if not messages:
            logger.warning("No messages found for cognitive analysis")
            return {"error": "No messages found for cognitive analysis"}
        
        # Analyze personality
        personality_results = await self.personality_analyzer.analyze(messages)
        
        # Analyze values
        values_results = await self.values_analyzer.analyze(messages)
        
        # Analyze decision-making
        decision_results = await self.decision_analyzer.analyze(messages)
        
        # Analyze memory
        memory_results = await self.memory_analyzer.analyze(messages)
        
        # Combine results
        results = {
            "personality": personality_results,
            "values": values_results,
            "decision": decision_results,
            "memory": memory_results
        }
        
        # Integrate with communication and advanced results if available
        integrated_results = await self._integrate_results(results, communication_results, advanced_results)
        
        # Store results
        self.analysis_results = results
        
        logger.info("Cognitive analysis complete")
        return results
    
    def _extract_messages(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract messages from data.
        
        Args:
            data: Data containing messages
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # If data is already a list of messages, return it
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        
        # If data is a dictionary with a 'messages' key, return that
        if isinstance(data, dict) and 'messages' in data:
            return data['messages']
        
        # If data is a dictionary with a 'data' key, try that
        if isinstance(data, dict) and 'data' in data:
            if isinstance(data['data'], list):
                return data['data']
            elif isinstance(data['data'], dict) and 'messages' in data['data']:
                return data['data']['messages']
        
        # If we couldn't extract messages, return empty list
        logger.warning("Could not extract messages from data")
        return []
    
    async def _integrate_results(self, cognitive_results: Dict[str, Any], 
                               communication_results: Optional[Dict[str, Any]] = None,
                               advanced_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Integrate cognitive results with communication and advanced results.
        
        Args:
            cognitive_results: Cognitive analysis results
            communication_results: Communication analysis results (optional)
            advanced_results: Advanced analysis results (optional)
            
        Returns:
            Dictionary of integrated results
        """
        integrated_results = cognitive_results.copy()
        
        # If communication results are available, integrate them
        if communication_results:
            # Extract relevant information from communication results
            if 'patterns' in communication_results:
                patterns = communication_results['patterns']
                if 'style' in patterns:
                    style = patterns['style']
                    # Integrate communication style with personality
                    if 'personality' in integrated_results:
                        if 'personality_profile' in integrated_results['personality']:
                            profile = integrated_results['personality']['personality_profile']
                            if 'communication_style' in profile:
                                profile['communication_style']['from_communication_analysis'] = style
        
        # If advanced results are available, integrate them
        if advanced_results:
            # Extract relevant information from advanced results
            if 'nlp' in advanced_results:
                nlp = advanced_results['nlp']
                if 'sentiment' in nlp:
                    sentiment = nlp['sentiment']
                    # Integrate sentiment with personality
                    if 'personality' in integrated_results:
                        if 'personality_profile' in integrated_results['personality']:
                            profile = integrated_results['personality']['personality_profile']
                            profile['sentiment_analysis'] = sentiment
        
        return integrated_results
    
    async def generate_insights(self, data: Any) -> List[Dict[str, Any]]:
        """
        Generate insights from cognitive analysis.
        
        Args:
            data: Data for analysis
            
        Returns:
            List of insights
        """
        logger.info("Generating cognitive insights")
        
        # Analyze data if not already analyzed
        if not self.analysis_results:
            await self.analyze(data)
        
        insights = []
        
        # Generate personality insights
        personality_insights = self._generate_personality_insights()
        insights.extend(personality_insights)
        
        # Generate values insights
        values_insights = self._generate_values_insights()
        insights.extend(values_insights)
        
        # Generate decision insights
        decision_insights = self._generate_decision_insights()
        insights.extend(decision_insights)
        
        # Generate memory insights
        memory_insights = self._generate_memory_insights()
        insights.extend(memory_insights)
        
        # Sort insights by score (higher is more important)
        sorted_insights = sorted(insights, key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Generated {len(sorted_insights)} cognitive insights")
        return sorted_insights
    
    def _generate_personality_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from personality analysis.
        
        Returns:
            List of personality insights
        """
        insights = []
        
        personality_results = self.analysis_results.get('personality', {})
        if not personality_results:
            return insights
        
        # Check if we have multiple senders or a single sender
        if personality_results.get('multiple_senders', False):
            profiles = personality_results.get('personality_profiles', {})
            for sender, profile in profiles.items():
                sender_insights = self._generate_personality_insights_from_profile(profile, sender)
                insights.extend(sender_insights)
        else:
            profile = personality_results.get('personality_profile', {})
            insights.extend(self._generate_personality_insights_from_profile(profile))
        
        return insights
    
    def _generate_personality_insights_from_profile(self, profile: Dict[str, Any], sender: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate insights from a personality profile.
        
        Args:
            profile: Personality profile
            sender: Sender name (optional)
            
        Returns:
            List of personality insights
        """
        insights = []
        
        # Add sender prefix if available
        prefix = f"{sender}: " if sender else ""
        
        # Big Five traits insights
        big_five_traits = profile.get('big_five_traits', {})
        if big_five_traits:
            # Find highest trait
            highest_trait = max(big_five_traits.items(), key=lambda x: x[1])
            
            # Find lowest trait
            lowest_trait = min(big_five_traits.items(), key=lambda x: x[1])
            
            # Generate insight for highest trait
            if highest_trait[1] > 0.7:
                trait_name = highest_trait[0].capitalize()
                description = ""
                if highest_trait[0] == 'openness':
                    description = "highly values creativity, innovation, and intellectual exploration"
                elif highest_trait[0] == 'conscientiousness':
                    description = "demonstrates strong organization, reliability, and attention to detail"
                elif highest_trait[0] == 'extraversion':
                    description = "shows high sociability, energy, and engagement with others"
                elif highest_trait[0] == 'agreeableness':
                    description = "exhibits strong cooperation, empathy, and consideration for others"
                elif highest_trait[0] == 'neuroticism':
                    description = "experiences heightened emotional sensitivity and reactivity"
                
                insights.append({
                    'type': 'personality',
                    'subtype': 'trait',
                    'title': f"{prefix}High {trait_name}",
                    'description': f"{prefix}Communication style {description}.",
                    'score': 0.8
                })
            
            # Generate insight for trait combination
            if big_five_traits.get('openness', 0) > 0.6 and big_five_traits.get('conscientiousness', 0) > 0.6:
                insights.append({
                    'type': 'personality',
                    'subtype': 'trait_combination',
                    'title': f"{prefix}Creative Problem-Solver",
                    'description': f"{prefix}Combines creativity with methodical approach to solve complex problems.",
                    'score': 0.7
                })
            elif big_five_traits.get('extraversion', 0) > 0.6 and big_five_traits.get('agreeableness', 0) > 0.6:
                insights.append({
                    'type': 'personality',
                    'subtype': 'trait_combination',
                    'title': f"{prefix}Social Connector",
                    'description': f"{prefix}Builds and maintains strong social connections through warmth and engagement.",
                    'score': 0.7
                })
        
        # Communication style insights
        communication_style = profile.get('communication_style', {})
        if communication_style:
            descriptors = communication_style.get('descriptors', [])
            if descriptors:
                if 'direct' in descriptors and 'formal' in descriptors:
                    insights.append({
                        'type': 'personality',
                        'subtype': 'communication',
                        'title': f"{prefix}Formal and Direct Communicator",
                        'description': f"{prefix}Communicates in a straightforward, structured manner with clear expectations.",
                        'score': 0.7
                    })
                elif 'expressive' in descriptors and 'casual' in descriptors:
                    insights.append({
                        'type': 'personality',
                        'subtype': 'communication',
                        'title': f"{prefix}Expressive and Casual Communicator",
                        'description': f"{prefix}Communicates with emotional openness and an informal, approachable style.",
                        'score': 0.7
                    })
        
        # Decision style insights
        decision_style = profile.get('decision_style', {})
        if decision_style:
            primary_style = decision_style.get('primary_style')
            if primary_style:
                insights.append({
                    'type': 'personality',
                    'subtype': 'decision',
                    'title': f"{prefix}{primary_style} Decision-Maker",
                    'description': f"{prefix}Approaches decisions with a {primary_style.lower()} style, focusing on {self._get_decision_style_focus(primary_style)}.",
                    'score': 0.6
                })
        
        return insights
    
    def _get_decision_style_focus(self, style: str) -> str:
        """Get the focus description for a decision style."""
        if style == 'Methodical':
            return "careful analysis and systematic evaluation"
        elif style == 'Logical':
            return "rational analysis and quick implementation"
        elif style == 'Reflective':
            return "thoughtful consideration of feelings and values"
        elif style == 'Instinctive':
            return "gut feelings and immediate impressions"
        else:
            return "balanced consideration of factors"
    
    def _generate_values_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from values analysis.
        
        Returns:
            List of values insights
        """
        insights = []
        
        values_results = self.analysis_results.get('values', {})
        if not values_results:
            return insights
        
        # Check if we have multiple senders or a single sender
        if values_results.get('multiple_senders', False):
            profiles = values_results.get('values_profiles', {})
            for sender, profile in profiles.items():
                sender_insights = self._generate_values_insights_from_profile(profile, sender)
                insights.extend(sender_insights)
        else:
            profile = values_results.get('values_profile', {})
            insights.extend(self._generate_values_insights_from_profile(profile))
        
        return insights
    
    def _generate_values_insights_from_profile(self, profile: Dict[str, Any], sender: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate insights from a values profile.
        
        Args:
            profile: Values profile
            sender: Sender name (optional)
            
        Returns:
            List of values insights
        """
        insights = []
        
        # Add sender prefix if available
        prefix = f"{sender}: " if sender else ""
        
        # Value priorities insights
        value_priorities = profile.get('value_priorities', {})
        if value_priorities:
            top_values = value_priorities.get('top_values', [])
            if top_values and len(top_values) >= 2:
                top_value1 = top_values[0]['value']
                top_value2 = top_values[1]['value']
                
                # Format value names
                top_value1_formatted = top_value1.replace('_', ' ').capitalize()
                top_value2_formatted = top_value2.replace('_', ' ').capitalize()
                
                insights.append({
                    'type': 'values',
                    'subtype': 'priorities',
                    'title': f"{prefix}Key Values: {top_value1_formatted} and {top_value2_formatted}",
                    'description': f"{prefix}Communication and decisions are strongly influenced by values of {top_value1_formatted.lower()} and {top_value2_formatted.lower()}.",
                    'score': 0.8
                })
            
            primary_orientation = value_priorities.get('primary_orientation')
            if primary_orientation:
                description = ""
                if primary_orientation == 'Self-Enhancement':
                    description = "personal achievement and influence"
                elif primary_orientation == 'Self-Transcendence':
                    description = "helping others and universal welfare"
                elif primary_orientation == 'Conservation':
                    description = "tradition, security, and conformity"
                elif primary_orientation == 'Openness to Change':
                    description = "independence, stimulation, and new experiences"
                
                insights.append({
                    'type': 'values',
                    'subtype': 'orientation',
                    'title': f"{prefix}Value Orientation: {primary_orientation}",
                    'description': f"{prefix}Demonstrates a strong orientation toward {description}.",
                    'score': 0.7
                })
            
            value_conflicts = value_priorities.get('value_conflicts', [])
            if value_conflicts:
                # Get the strongest conflict
                strongest_conflict = max(value_conflicts, key=lambda x: x.get('strength', 0))
                conflict_values = strongest_conflict.get('values', [])
                if len(conflict_values) >= 2:
                    value1 = conflict_values[0].replace('_', ' ').capitalize()
                    value2 = conflict_values[1].replace('_', ' ').capitalize()
                    
                    insights.append({
                        'type': 'values',
                        'subtype': 'conflict',
                        'title': f"{prefix}Value Tension: {value1} vs. {value2}",
                        'description': f"{prefix}Shows tension between competing values of {value1.lower()} and {value2.lower()}, which may create decision challenges.",
                        'score': 0.6
                    })
        
        # Moral foundations insights
        moral_foundations = profile.get('moral_foundations', {})
        if moral_foundations:
            # Find highest moral foundation
            highest_foundation = max(moral_foundations.items(), key=lambda x: x[1])
            
            if highest_foundation[1] > 0.25:  # Only if it's significantly high
                foundation_name = highest_foundation[0].replace('_', '/').capitalize()
                
                description = ""
                if highest_foundation[0] == 'care_harm':
                    description = "compassion and protection from harm"
                elif highest_foundation[0] == 'fairness_cheating':
                    description = "justice, rights, and equality"
                elif highest_foundation[0] == 'loyalty_betrayal':
                    description = "group loyalty and solidarity"
                elif highest_foundation[0] == 'authority_subversion':
                    description = "respect for authority and tradition"
                elif highest_foundation[0] == 'sanctity_degradation':
                    description = "purity and avoiding moral contamination"
                elif highest_foundation[0] == 'liberty_oppression':
                    description = "freedom and resistance to oppression"
                
                insights.append({
                    'type': 'values',
                    'subtype': 'moral',
                    'title': f"{prefix}Strong {foundation_name} Foundation",
                    'description': f"{prefix}Shows strong moral emphasis on {description}.",
                    'score': 0.7
                })
        
        return insights
    
    def _generate_decision_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from decision analysis.
        
        Returns:
            List of decision insights
        """
        insights = []
        
        decision_results = self.analysis_results.get('decision', {})
        if not decision_results:
            return insights
        
        # Check if we have multiple senders or a single sender
        if decision_results.get('multiple_senders', False):
            profiles = decision_results.get('decision_profiles', {})
            for sender, profile in profiles.items():
                sender_insights = self._generate_decision_insights_from_profile(profile, sender)
                insights.extend(sender_insights)
        else:
            profile = decision_results.get('decision_profile', {})
            insights.extend(self._generate_decision_insights_from_profile(profile))
        
        return insights
    
    def _generate_decision_insights_from_profile(self, profile: Dict[str, Any], sender: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate insights from a decision profile.
        
        Args:
            profile: Decision profile
            sender: Sender name (optional)
            
        Returns:
            List of decision insights
        """
        insights = []
        
        # Add sender prefix if available
        prefix = f"{sender}: " if sender else ""
        
        # Decision styles insights
        decision_styles = profile.get('decision_styles', {})
        if decision_styles:
            primary_style = decision_styles.get('primary_style')
            secondary_style = decision_styles.get('secondary_style')
            
            if primary_style and secondary_style:
                insights.append({
                    'type': 'decision',
                    'subtype': 'style',
                    'title': f"{prefix}{primary_style.capitalize()}-{secondary_style.capitalize()} Decision Approach",
                    'description': f"{prefix}Primarily uses a {primary_style} approach to decisions, complemented by {secondary_style} elements.",
                    'score': 0.7
                })
            
            dimensions = decision_styles.get('dimensions', {})
            if dimensions:
                analytical_intuitive = dimensions.get('analytical_intuitive')
                deliberate_spontaneous = dimensions.get('deliberate_spontaneous')
                
                if analytical_intuitive is not None and deliberate_spontaneous is not None:
                    if analytical_intuitive > 0.3 and deliberate_spontaneous > 0.3:
                        insights.append({
                            'type': 'decision',
                            'subtype': 'approach',
                            'title': f"{prefix}Methodical Analyzer",
                            'description': f"{prefix}Takes a careful, analytical approach to decisions, thoroughly examining options before acting.",
                            'score': 0.7
                        })
                    elif analytical_intuitive > 0.3 and deliberate_spontaneous < -0.3:
                        insights.append({
                            'type': 'decision',
                            'subtype': 'approach',
                            'title': f"{prefix}Quick Analyzer",
                            'description': f"{prefix}Rapidly analyzes situations and makes quick decisions based on logical assessment.",
                            'score': 0.7
                        })
                    elif analytical_intuitive < -0.3 and deliberate_spontaneous > 0.3:
                        insights.append({
                            'type': 'decision',
                            'subtype': 'approach',
                            'title': f"{prefix}Thoughtful Intuitive",
                            'description': f"{prefix}Relies on intuition but takes time to reflect before making decisions.",
                            'score': 0.7
                        })
                    elif analytical_intuitive < -0.3 and deliberate_spontaneous < -0.3:
                        insights.append({
                            'type': 'decision',
                            'subtype': 'approach',
                            'title': f"{prefix}Spontaneous Intuitive",
                            'description': f"{prefix}Makes quick decisions based on gut feelings and immediate impressions.",
                            'score': 0.7
                        })
        
        # Decision processes insights
        decision_processes = profile.get('decision_processes', {})
        if decision_processes:
            process_focus = decision_processes.get('process_focus')
            process_completeness = decision_processes.get('process_completeness')
            
            if process_focus:
                insights.append({
                    'type': 'decision',
                    'subtype': 'process',
                    'title': f"{prefix}{process_focus} Decision Focus",
                    'description': f"{prefix}Emphasizes the {process_focus.lower()} phase of decision-making.",
                    'score': 0.6
                })
            
            if process_completeness is not None:
                if process_completeness:
                    insights.append({
                        'type': 'decision',
                        'subtype': 'process',
                        'title': f"{prefix}Comprehensive Decision Process",
                        'description': f"{prefix}Demonstrates a thorough decision-making process that covers all stages from problem identification to review.",
                        'score': 0.6
                    })
                else:
                    insights.append({
                        'type': 'decision',
                        'subtype': 'process',
                        'title': f"{prefix}Selective Decision Process",
                        'description': f"{prefix}Focuses on specific aspects of decision-making while giving less attention to others.",
                        'score': 0.6
                    })
        
        # Decision biases insights
        decision_biases = profile.get('decision_biases', {})
        if decision_biases:
            primary_bias = decision_biases.get('primary_bias', {})
            bias_susceptibility = decision_biases.get('bias_susceptibility')
            
            if primary_bias and bias_susceptibility and bias_susceptibility != 'Low':
                bias_name = primary_bias.get('bias', '').replace('_', ' ').capitalize()
                
                insights.append({
                    'type': 'decision',
                    'subtype': 'bias',
                    'title': f"{prefix}{bias_name} Bias Tendency",
                    'description': f"{prefix}Shows a {bias_susceptibility.lower()} susceptibility to {bias_name.lower()} bias in decision-making.",
                    'score': 0.7 if bias_susceptibility == 'High' else 0.6
                })
        
        # Decision complexity insights
        decision_complexity = profile.get('decision_complexity', {})
        if decision_complexity:
            complexity_level = decision_complexity.get('complexity_level')
            
            if complexity_level and complexity_level != 'Moderate':
                insights.append({
                    'type': 'decision',
                    'subtype': 'complexity',
                    'title': f"{prefix}{complexity_level} Decision Complexity",
                    'description': f"{prefix}Approaches decisions with {complexity_level.lower()} complexity, " + 
                                  ("considering many factors and contingencies." if complexity_level == 'High' else "focusing on straightforward factors."),
                    'score': 0.6
                })
        
        return insights
    
    def _generate_memory_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from memory analysis.
        
        Returns:
            List of memory insights
        """
        insights = []
        
        memory_results = self.analysis_results.get('memory', {})
        if not memory_results:
            return insights
        
        # Recall patterns insights
        recall_patterns = memory_results.get('recall_patterns', {})
        if recall_patterns:
            recall_tendency = recall_patterns.get('recall_tendency')
            positive_recall_ratio = recall_patterns.get('positive_recall_ratio')
            
            if recall_tendency:
                insights.append({
                    'type': 'memory',
                    'subtype': 'recall',
                    'title': f"{recall_tendency}",
                    'description': f"Demonstrates {recall_tendency.lower()} in communication, " + 
                                  ("frequently referencing past information." if 'Recall' in recall_tendency else "often noting forgotten details."),
                    'score': 0.7
                })
        
        # Reference patterns insights
        reference_patterns = memory_results.get('reference_patterns', {})
        if reference_patterns:
            time_references = reference_patterns.get('time_references', {})
            if time_references:
                time_orientation = time_references.get('time_orientation')
                
                if time_orientation:
                    insights.append({
                        'type': 'memory',
                        'subtype': 'time_orientation',
                        'title': f"{time_orientation} Time Perspective",
                        'description': f"Communication primarily focuses on {time_orientation.lower().replace('-', ' ')} events and experiences.",
                        'score': 0.6
                    })
            
            personal_references = reference_patterns.get('personal_references', {})
            if personal_references:
                personal_reference_orientation = personal_references.get('personal_reference_orientation')
                
                if personal_reference_orientation:
                    insights.append({
                        'type': 'memory',
                        'subtype': 'reference_focus',
                        'title': f"{personal_reference_orientation} Reference Style",
                        'description': self._get_reference_style_description(personal_reference_orientation),
                        'score': 0.6
                    })
        
        # Memory consistency insights
        memory_consistency = memory_results.get('memory_consistency', {})
        if memory_consistency:
            consistency_level = memory_consistency.get('consistency_level')
            
            if consistency_level and consistency_level != 'Moderate':
                insights.append({
                    'type': 'memory',
                    'subtype': 'consistency',
                    'title': f"{consistency_level} Memory Consistency",
                    'description': f"Demonstrates {consistency_level.lower()} consistency in recalling and referencing information.",
                    'score': 0.7 if consistency_level == 'Low' else 0.6
                })
        
        # Memory decay insights
        memory_decay = memory_results.get('memory_decay', {})
        if memory_decay:
            retention_level = memory_decay.get('retention_level')
            
            if retention_level and retention_level != 'Moderate':
                insights.append({
                    'type': 'memory',
                    'subtype': 'retention',
                    'title': f"{retention_level} Information Retention",
                    'description': f"Shows {retention_level.lower()} retention of previously discussed information over time.",
                    'score': 0.7 if retention_level == 'Low' else 0.6
                })
        
        return insights
    
    def _get_reference_style_description(self, style: str) -> str:
        """Get the description for a reference style."""
        if style == 'Self-Focused':
            return "Communication primarily references personal experiences and perspectives."
        elif style == 'Other-Focused':
            return "Communication primarily addresses and references the other person directly."
        elif style == 'External-Focused':
            return "Communication primarily references external people, events, and topics."
        else:
            return "Communication shows a balanced reference style."