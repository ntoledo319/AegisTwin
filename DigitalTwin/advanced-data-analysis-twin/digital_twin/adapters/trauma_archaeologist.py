"""
Trauma Pattern Analyzer Adapter for the Digital Twin.

This module provides an adapter for integrating SpiderMind Omega's TraumaArchaeologist
with the Digital Twin system for psychological pattern detection and healing pathway generation.
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional
import importlib.util
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class TraumaPatternAnalyzer:
    """
    Adapter for SpiderMind Omega's TraumaArchaeologist for psychological pattern detection
    and healing pathway generation.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the trauma pattern analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.trauma_archaeologist = None
        self.trauma_structures = None
        self._initialize_trauma_archaeologist()
        logger.info("Trauma Pattern Analyzer initialized")

    def _initialize_trauma_archaeologist(self) -> None:
        """
        Initialize TraumaArchaeologist from SpiderMind Omega.
        """
        try:
            # Try to import TraumaArchaeologist from SpiderMind Omega
            spidermind_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ct_omega"))
            
            if spidermind_path not in sys.path:
                sys.path.append(spidermind_path)
                
            # Try to import the TraumaArchaeologist class
            spec = importlib.util.find_spec("core.trauma_archaeologist")
            if spec:
                trauma_archaeologist_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(trauma_archaeologist_module)
                self.trauma_archaeologist = trauma_archaeologist_module.TraumaArchaeologist()
                self.trauma_structures = trauma_archaeologist_module
                logger.info("Successfully imported TraumaArchaeologist from SpiderMind Omega")
            else:
                logger.warning("Could not find TraumaArchaeologist module in SpiderMind Omega")
                self.trauma_archaeologist = None
                self.trauma_structures = None
                
        except Exception as e:
            logger.error(f"Error initializing TraumaArchaeologist: {str(e)}")
            logger.warning("Using fallback trauma pattern analysis")
            self.trauma_archaeologist = None
            self.trauma_structures = None

    async def analyze_trauma_patterns(self, consciousness_states: List[Dict[str, Any]], excavation_depth: int = None) -> Dict[str, Any]:
        """
        Analyze trauma patterns in consciousness states.

        Args:
            consciousness_states: List of consciousness states to analyze
            excavation_depth: How deep to excavate trauma patterns

        Returns:
            Dictionary of trauma pattern analysis results
        """
        # If TraumaArchaeologist is available, use it
        if self.trauma_archaeologist:
            try:
                # Excavate trauma patterns
                excavation_report = await self.trauma_archaeologist.excavate_trauma_patterns(
                    consciousness_states, excavation_depth
                )
                
                # Convert results to our format
                return self._convert_from_excavation_report(excavation_report)
            except Exception as e:
                logger.error(f"Error using TraumaArchaeologist: {str(e)}")
                logger.warning("Falling back to basic trauma pattern analysis")
                
        # Fallback: Use basic trauma pattern analysis
        return self._basic_trauma_pattern_analysis(consciousness_states)

    async def generate_healing_pathways(self, trauma_signatures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate healing pathways for detected trauma signatures.

        Args:
            trauma_signatures: List of trauma signatures

        Returns:
            List of healing pathways
        """
        # If TraumaArchaeologist is available, use it
        if self.trauma_archaeologist:
            try:
                # Convert trauma signatures to TraumaSignature objects
                trauma_signature_objects = [self._convert_to_trauma_signature(sig) for sig in trauma_signatures]
                
                # Generate healing pathways
                healing_pathways = await self.trauma_archaeologist._generate_healing_pathways(trauma_signature_objects)
                
                # Convert results to our format
                return [self._convert_from_healing_pathway(pathway) for pathway in healing_pathways]
            except Exception as e:
                logger.error(f"Error generating healing pathways: {str(e)}")
                logger.warning("Falling back to basic healing pathway generation")
                
        # Fallback: Use basic healing pathway generation
        return self._basic_healing_pathway_generation(trauma_signatures)

    async def facilitate_healing(self, trauma_signature_ids: List[str], healing_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Facilitate healing for identified trauma signatures.

        Args:
            trauma_signature_ids: List of trauma signature IDs
            healing_preferences: Healing preferences

        Returns:
            Dictionary of healing results
        """
        # If TraumaArchaeologist is available, use it
        if self.trauma_archaeologist:
            try:
                # Facilitate trauma healing
                healing_results = await self.trauma_archaeologist.facilitate_trauma_healing(
                    trauma_signature_ids, healing_preferences
                )
                
                # Convert results to our format
                return self._convert_from_healing_results(healing_results)
            except Exception as e:
                logger.error(f"Error facilitating healing: {str(e)}")
                logger.warning("Falling back to basic healing facilitation")
                
        # Fallback: Use basic healing facilitation
        return self._basic_healing_facilitation(trauma_signature_ids, healing_preferences)

    def _convert_to_consciousness_states(self, digital_twin_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Digital Twin states to consciousness states for TraumaArchaeologist.

        Args:
            digital_twin_states: List of Digital Twin states

        Returns:
            List of consciousness states
        """
        consciousness_states = []
        
        for state in digital_twin_states:
            # Extract personality dimensions
            personality = state.get('personality', {})
            dimensions = personality.get('dimensions', {})
            traits = personality.get('traits', {})
            
            # Extract memory information
            memory = state.get('memory', {})
            episodic_memories = memory.get('episodic', [])
            
            # Create consciousness dimensions
            consciousness_dimensions = {
                'emotional': dimensions.get('neuroticism', 0.5),
                'cognitive': dimensions.get('openness', 0.5),
                'social': dimensions.get('extraversion', 0.5),
                'ethical': dimensions.get('agreeableness', 0.5),
                'disciplinary': dimensions.get('conscientiousness', 0.5)
            }
            
            # Extract emotions from recent memories
            emotions = []
            triggers = []
            if episodic_memories:
                recent_memories = sorted(episodic_memories, key=lambda m: m.get('timestamp', ''), reverse=True)[:5]
                for memory in recent_memories:
                    if 'emotions' in memory:
                        for emotion in memory.get('emotions', []):
                            emotions.append({
                                'type': emotion.get('type', 'unknown'),
                                'intensity': emotion.get('intensity', 0.5),
                                'context': memory.get('context', {})
                            })
                    if 'context' in memory and 'trigger' in memory.get('context', {}):
                        triggers.append(memory.get('context', {}).get('trigger', 'unknown_trigger'))
            
            # Create consciousness state
            consciousness_state = {
                'profile_id': state.get('user_id', 'unknown_user'),
                'timestamp': state.get('timestamp', datetime.now().isoformat()),
                'dimensions': consciousness_dimensions,
                'mood_level': 5.0 - (dimensions.get('neuroticism', 0.5) * 5.0),  # Convert neuroticism to mood (0-5 scale)
                'anxiety_level': dimensions.get('neuroticism', 0.5) * 5.0,  # Convert neuroticism to anxiety (0-5 scale)
                'focus_level': dimensions.get('conscientiousness', 0.5) * 5.0,  # Convert conscientiousness to focus (0-5 scale)
                'triggers': triggers,
                'emotions': emotions,
                'coherence': state.get('coherence', 0.5),
                'metadata': {
                    'source': 'digital_twin',
                    'state_type': 'personality_snapshot'
                }
            }
            
            consciousness_states.append(consciousness_state)
        
        return consciousness_states

    def _convert_from_excavation_report(self, excavation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert TraumaArchaeologist excavation report to our format.

        Args:
            excavation_report: TraumaArchaeologist excavation report

        Returns:
            Excavation report in our format
        """
        # Convert trauma signatures
        trauma_signatures = []
        for signature in excavation_report.get('excavation_summary', {}).get('trauma_signatures', []):
            if hasattr(signature, 'signature_id'):
                # Convert from TraumaSignature object
                trauma_signatures.append({
                    'signature_id': signature.signature_id,
                    'trauma_type': signature.trauma_type.value,
                    'severity': signature.severity,
                    'age_estimate': signature.age_estimate,
                    'affected_dimensions': signature.affected_dimensions,
                    'core_wound': signature.core_wound,
                    'protective_mechanisms': signature.protective_mechanisms,
                    'trigger_patterns': signature.trigger_patterns,
                    'healing_indicators': signature.healing_indicators,
                    'energy_signature': signature.energy_signature,
                    'metadata': signature.metadata
                })
            else:
                # Already a dictionary
                trauma_signatures.append(signature)
        
        # Convert healing pathways
        healing_pathways = []
        for pathway in excavation_report.get('healing_pathways', []):
            if hasattr(pathway, 'pathway_id'):
                # Convert from HealingPathway object
                healing_pathways.append({
                    'pathway_id': pathway.pathway_id,
                    'trauma_signature_id': pathway.trauma_signature_id,
                    'healing_approach': pathway.healing_approach,
                    'estimated_duration': pathway.estimated_duration,
                    'success_probability': pathway.success_probability,
                    'required_resources': pathway.required_resources,
                    'healing_stages': pathway.healing_stages,
                    'integration_markers': pathway.integration_markers,
                    'resistance_factors': pathway.resistance_factors,
                    'support_requirements': pathway.support_requirements,
                    'metadata': pathway.metadata
                })
            else:
                # Already a dictionary
                healing_pathways.append(pathway)
        
        return {
            'timestamp': excavation_report.get('timestamp', datetime.now().isoformat()),
            'excavation_depth': excavation_report.get('excavation_depth', 0),
            'layers_analyzed': excavation_report.get('layers_analyzed', 0),
            'trauma_signatures_found': excavation_report.get('trauma_signatures_found', 0),
            'healing_pathways_identified': excavation_report.get('healing_pathways_identified', 0),
            'trauma_signatures': trauma_signatures,
            'healing_pathways': healing_pathways,
            'cross_layer_patterns': excavation_report.get('excavation_summary', {}).get('cross_layer_patterns', []),
            'integration_opportunities': excavation_report.get('integration_opportunities', []),
            'healing_potential': excavation_report.get('consciousness_healing_potential', 0.5),
            'recommendations': excavation_report.get('recommendations', [])
        }

    def _convert_to_trauma_signature(self, signature_dict: Dict[str, Any]):
        """
        Convert trauma signature dictionary to TraumaSignature object.

        Args:
            signature_dict: Trauma signature dictionary

        Returns:
            TraumaSignature object or None if conversion fails
        """
        if not self.trauma_structures:
            return None
        
        try:
            # Get trauma type enum
            trauma_type_str = signature_dict.get('trauma_type', 'relational')
            trauma_type = self._get_trauma_type(trauma_type_str)
            
            # Create TraumaSignature object
            return self.trauma_structures.TraumaSignature(
                signature_id=signature_dict.get('signature_id', str(uuid.uuid4())),
                trauma_type=trauma_type,
                severity=signature_dict.get('severity', 0.5),
                age_estimate=signature_dict.get('age_estimate', 30),
                affected_dimensions=signature_dict.get('affected_dimensions', []),
                core_wound=signature_dict.get('core_wound', ''),
                protective_mechanisms=signature_dict.get('protective_mechanisms', []),
                trigger_patterns=signature_dict.get('trigger_patterns', []),
                healing_indicators=signature_dict.get('healing_indicators', []),
                energy_signature=signature_dict.get('energy_signature', {}),
                metadata=signature_dict.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Error converting trauma signature: {str(e)}")
            return None

    def _convert_from_healing_pathway(self, pathway) -> Dict[str, Any]:
        """
        Convert HealingPathway object to dictionary.

        Args:
            pathway: HealingPathway object

        Returns:
            Dictionary representation of healing pathway
        """
        if hasattr(pathway, 'pathway_id'):
            return {
                'pathway_id': pathway.pathway_id,
                'trauma_signature_id': pathway.trauma_signature_id,
                'healing_approach': pathway.healing_approach,
                'estimated_duration': pathway.estimated_duration,
                'success_probability': pathway.success_probability,
                'required_resources': pathway.required_resources,
                'healing_stages': pathway.healing_stages,
                'integration_markers': pathway.integration_markers,
                'resistance_factors': pathway.resistance_factors,
                'support_requirements': pathway.support_requirements,
                'metadata': pathway.metadata
            }
        else:
            return pathway

    def _convert_from_healing_results(self, healing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert healing results to our format.

        Args:
            healing_results: Healing results from TraumaArchaeologist

        Returns:
            Healing results in our format
        """
        return {
            'timestamp': healing_results.get('timestamp', datetime.now().isoformat()),
            'trauma_signatures_addressed': healing_results.get('trauma_signatures_addressed', 0),
            'healing_sessions': healing_results.get('healing_sessions', []),
            'integration_progress': healing_results.get('integration_progress', {}),
            'overall_healing_score': healing_results.get('overall_healing_score', 0.0)
        }

    def _get_trauma_type(self, trauma_type_str: str):
        """
        Convert trauma type string to TraumaType enum.

        Args:
            trauma_type_str: Trauma type string

        Returns:
            TraumaType enum value
        """
        if self.trauma_structures:
            trauma_map = {
                'acute': self.trauma_structures.TraumaType.ACUTE,
                'chronic': self.trauma_structures.TraumaType.CHRONIC,
                'developmental': self.trauma_structures.TraumaType.DEVELOPMENTAL,
                'relational': self.trauma_structures.TraumaType.RELATIONAL,
                'existential': self.trauma_structures.TraumaType.EXISTENTIAL,
                'somatic': self.trauma_structures.TraumaType.SOMATIC,
                'collective': self.trauma_structures.TraumaType.COLLECTIVE
            }
            return trauma_map.get(trauma_type_str.lower(), self.trauma_structures.TraumaType.RELATIONAL)
        else:
            return trauma_type_str

    def _basic_trauma_pattern_analysis(self, consciousness_states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform basic trauma pattern analysis without SpiderMind components.

        Args:
            consciousness_states: List of consciousness states

        Returns:
            Basic trauma pattern analysis results
        """
        if len(consciousness_states) < 5:
            return {
                'timestamp': datetime.now().isoformat(),
                'excavation_depth': 0,
                'layers_analyzed': 0,
                'trauma_signatures_found': 0,
                'healing_pathways_identified': 0,
                'trauma_signatures': [],
                'healing_pathways': [],
                'cross_layer_patterns': [],
                'integration_opportunities': [],
                'healing_potential': 0.5,
                'recommendations': [{
                    'priority': 'medium',
                    'type': 'data_collection',
                    'description': 'Insufficient data for trauma pattern analysis',
                    'actions': [
                        'Collect more consciousness data',
                        'Increase emotional state sampling',
                        'Track trigger-response patterns'
                    ]
                }]
            }
        
        # Sort states chronologically
        sorted_states = sorted(consciousness_states, key=lambda s: s.get('timestamp', ''))
        
        # Divide into layers (time periods)
        layers = []
        layer_size = max(1, len(sorted_states) // 3)
        for i in range(0, len(sorted_states), layer_size):
            layer = sorted_states[i:i + layer_size]
            if layer:
                layers.append(layer)
        
        # Analyze emotional volatility
        trauma_signatures = []
        
        for layer_idx, layer in enumerate(layers):
            # Extract emotional dimensions
            emotional_values = []
            for state in layer:
                dimensions = state.get('dimensions', {})
                emotional_value = dimensions.get('emotional', 0.5)
                emotional_values.append(emotional_value)
            
            # Check for volatility
            if len(emotional_values) >= 3:
                volatility = self._calculate_volatility(emotional_values)
                
                # Check for trauma indicators
                if volatility > 0.2:
                    # Detect sudden drops
                    drops = []
                    for i in range(1, len(emotional_values)):
                        drop = emotional_values[i-1] - emotional_values[i]
                        if drop > 0.3:  # Significant drop threshold
                            drops.append(i)
                    
                    # Detect suppression patterns
                    low_values = [v for v in emotional_values if v < 0.3]
                    suppression_ratio = len(low_values) / len(emotional_values)
                    
                    # Determine trauma type and severity
                    if len(drops) > 0:
                        trauma_type = 'acute'
                        severity = 0.7
                    elif suppression_ratio > 0.5:
                        trauma_type = 'chronic'
                        severity = 0.6
                    else:
                        trauma_type = 'relational'
                        severity = 0.5
                    
                    # Create trauma signature
                    signature_id = str(uuid.uuid4())
                    trauma_signatures.append({
                        'signature_id': signature_id,
                        'trauma_type': trauma_type,
                        'severity': severity,
                        'age_estimate': layer_idx * 30,  # Rough estimate: 30 days per layer
                        'affected_dimensions': ['emotional', 'social'],
                        'core_wound': self._determine_core_wound(trauma_type),
                        'protective_mechanisms': self._determine_protective_mechanisms(trauma_type),
                        'trigger_patterns': self._extract_triggers(layer),
                        'healing_indicators': ['emotional_stability', 'trigger_resilience'],
                        'energy_signature': {'emotional': 0.8, 'cognitive': 0.4},
                        'metadata': {
                            'layer_index': layer_idx,
                            'detection_timestamp': datetime.now().isoformat(),
                            'volatility': volatility,
                            'suppression_ratio': suppression_ratio
                        }
                    })
        
        # Generate healing pathways
        healing_pathways = self._basic_healing_pathway_generation(trauma_signatures)
        
        # Calculate healing potential
        healing_potential = 0.7 - (sum(s['severity'] for s in trauma_signatures) / max(1, len(trauma_signatures)) * 0.4)
        
        # Generate recommendations
        recommendations = []
        
        if trauma_signatures:
            severe_signatures = [s for s in trauma_signatures if s['severity'] >= 0.7]
            
            if severe_signatures:
                recommendations.append({
                    'priority': 'high',
                    'type': 'trauma_awareness',
                    'description': f'Address {len(severe_signatures)} significant emotional pattern disruptions',
                    'actions': [
                        'Implement emotional stabilization techniques',
                        'Identify and manage emotional triggers',
                        'Consider professional support for emotional processing'
                    ]
                })
            else:
                recommendations.append({
                    'priority': 'medium',
                    'type': 'emotional_integration',
                    'description': 'Support integration of emotional patterns',
                    'actions': [
                        'Practice emotional awareness techniques',
                        'Develop trigger management strategies',
                        'Strengthen emotional resilience'
                    ]
                })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'excavation_depth': len(layers),
            'layers_analyzed': len(layers),
            'trauma_signatures_found': len(trauma_signatures),
            'healing_pathways_identified': len(healing_pathways),
            'trauma_signatures': trauma_signatures,
            'healing_pathways': healing_pathways,
            'cross_layer_patterns': self._identify_cross_layer_patterns(trauma_signatures),
            'integration_opportunities': self._identify_integration_opportunities(trauma_signatures),
            'healing_potential': healing_potential,
            'recommendations': recommendations
        }

    def _basic_healing_pathway_generation(self, trauma_signatures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate basic healing pathways without SpiderMind components.

        Args:
            trauma_signatures: List of trauma signatures

        Returns:
            List of healing pathways
        """
        healing_pathways = []
        
        for signature in trauma_signatures:
            signature_id = signature.get('signature_id', str(uuid.uuid4()))
            trauma_type = signature.get('trauma_type', 'relational')
            severity = signature.get('severity', 0.5)
            
            # Determine healing approach based on trauma type
            if trauma_type == 'acute':
                healing_approach = 'emotional_processing'
                estimated_duration = 30  # 30 days
                success_probability = 0.8
            elif trauma_type == 'chronic':
                healing_approach = 'pattern_recognition'
                estimated_duration = 90  # 90 days
                success_probability = 0.6
            elif trauma_type == 'developmental':
                healing_approach = 'inner_child_work'
                estimated_duration = 180  # 180 days
                success_probability = 0.5
            else:
                healing_approach = 'relational_healing'
                estimated_duration = 60  # 60 days
                success_probability = 0.7
            
            # Adjust based on severity
            estimated_duration = int(estimated_duration * (0.5 + severity))
            success_probability = success_probability * (1.0 - (severity * 0.3))
            
            # Create healing stages
            healing_stages = [
                {
                    'stage': 'awareness',
                    'description': 'Developing awareness of patterns',
                    'duration': int(estimated_duration * 0.2),
                    'completion_criteria': ['Pattern recognition', 'Emotional awareness']
                },
                {
                    'stage': 'processing',
                    'description': 'Processing emotional content',
                    'duration': int(estimated_duration * 0.4),
                    'completion_criteria': ['Emotional release', 'Cognitive reframing']
                },
                {
                    'stage': 'integration',
                    'description': 'Integrating new patterns',
                    'duration': int(estimated_duration * 0.4),
                    'completion_criteria': ['New behavior patterns', 'Reduced trigger reactivity']
                }
            ]
            
            # Create healing pathway
            healing_pathways.append({
                'pathway_id': str(uuid.uuid4()),
                'trauma_signature_id': signature_id,
                'healing_approach': healing_approach,
                'estimated_duration': estimated_duration,
                'success_probability': success_probability,
                'required_resources': ['emotional_awareness', 'self_reflection', 'social_support'],
                'healing_stages': healing_stages,
                'integration_markers': ['emotional_stability', 'trigger_resilience', 'behavioral_flexibility'],
                'resistance_factors': ['avoidance', 'denial', 'overwhelm'],
                'support_requirements': ['consistency', 'safety', 'validation'],
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'trauma_type': trauma_type,
                    'severity': severity
                }
            })
        
        return healing_pathways

    def _basic_healing_facilitation(self, trauma_signature_ids: List[str], healing_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform basic healing facilitation without SpiderMind components.

        Args:
            trauma_signature_ids: List of trauma signature IDs
            healing_preferences: Healing preferences

        Returns:
            Basic healing facilitation results
        """
        healing_preferences = healing_preferences or {}
        
        healing_sessions = []
        integration_progress = {}
        
        for signature_id in trauma_signature_ids:
            # Simulate a healing session
            session_result = {
                'signature_id': signature_id,
                'session_timestamp': datetime.now().isoformat(),
                'approach_used': healing_preferences.get('approach', 'emotional_processing'),
                'session_duration': 60,  # 60 minutes
                'current_stage': 'awareness',
                'integration_score': 0.3,  # Initial progress
                'remaining_stages': ['processing', 'integration'],
                'insights_gained': [
                    'Identified emotional trigger patterns',
                    'Recognized protective mechanisms'
                ],
                'next_steps': [
                    'Continue emotional awareness practice',
                    'Begin trigger management techniques'
                ]
            }
            
            healing_sessions.append(session_result)
            
            # Track integration progress
            integration_progress[signature_id] = {
                'healing_stage': session_result['current_stage'],
                'integration_score': session_result['integration_score'],
                'remaining_work': len(session_result['remaining_stages'])
            }
        
        # Calculate overall healing score
        overall_healing_score = 0.0
        if healing_sessions:
            integration_scores = [session['integration_score'] for session in healing_sessions]
            overall_healing_score = sum(integration_scores) / len(integration_scores)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'trauma_signatures_addressed': len(trauma_signature_ids),
            'healing_sessions': healing_sessions,
            'integration_progress': integration_progress,
            'overall_healing_score': overall_healing_score
        }

    def _calculate_volatility(self, values: List[float]) -> float:
        """
        Calculate volatility of a series of values.

        Args:
            values: List of values

        Returns:
            Volatility score
        """
        if len(values) < 2:
            return 0.0
        
        changes = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        return sum(changes) / (len(values) - 1)

    def _determine_core_wound(self, trauma_type: str) -> str:
        """
        Determine core wound based on trauma type.

        Args:
            trauma_type: Type of trauma

        Returns:
            Core wound description
        """
        wound_map = {
            'acute': 'betrayal',
            'chronic': 'powerlessness',
            'developmental': 'abandonment',
            'relational': 'rejection',
            'existential': 'meaninglessness',
            'somatic': 'violation',
            'collective': 'disconnection'
        }
        
        return wound_map.get(trauma_type, 'unworthiness')

    def _determine_protective_mechanisms(self, trauma_type: str) -> List[str]:
        """
        Determine protective mechanisms based on trauma type.

        Args:
            trauma_type: Type of trauma

        Returns:
            List of protective mechanisms
        """
        mechanism_map = {
            'acute': ['avoidance', 'hypervigilance'],
            'chronic': ['numbing', 'dissociation'],
            'developmental': ['people-pleasing', 'perfectionism'],
            'relational': ['isolation', 'distrust'],
            'existential': ['distraction', 'nihilism'],
            'somatic': ['disconnection', 'control'],
            'collective': ['denial', 'projection']
        }
        
        return mechanism_map.get(trauma_type, ['rationalization', 'minimization'])

    def _extract_triggers(self, layer: List[Dict[str, Any]]) -> List[str]:
        """
        Extract triggers from a layer of consciousness states.

        Args:
            layer: Layer of consciousness states

        Returns:
            List of triggers
        """
        triggers = []
        
        for state in layer:
            if 'triggers' in state:
                triggers.extend(state.get('triggers', []))
        
        # Remove duplicates and return
        return list(set(triggers))

    def _identify_cross_layer_patterns(self, trauma_signatures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify patterns across trauma signatures.

        Args:
            trauma_signatures: List of trauma signatures

        Returns:
            List of cross-layer patterns
        """
        if not trauma_signatures:
            return []
        
        # Group signatures by trauma type
        type_groups = {}
        for sig in trauma_signatures:
            trauma_type = sig.get('trauma_type', 'unknown')
            if trauma_type not in type_groups:
                type_groups[trauma_type] = []
            type_groups[trauma_type].append(sig)
        
        patterns = []
        
        # Analyze each type group
        for trauma_type, signatures in type_groups.items():
            if len(signatures) >= 2:
                # Calculate average severity
                avg_severity = sum(sig.get('severity', 0.5) for sig in signatures) / len(signatures)
                
                # Collect affected dimensions
                all_dimensions = []
                for sig in signatures:
                    all_dimensions.extend(sig.get('affected_dimensions', []))
                
                # Count dimension frequency
                dimension_counts = {}
                for dim in all_dimensions:
                    if dim not in dimension_counts:
                        dimension_counts[dim] = 0
                    dimension_counts[dim] += 1
                
                # Find most common dimensions
                common_dimensions = sorted(dimension_counts.items(), key=lambda x: x[1], reverse=True)
                common_dimensions = [dim for dim, count in common_dimensions if count >= len(signatures) / 2]
                
                patterns.append({
                    'pattern_id': str(uuid.uuid4()),
                    'trauma_type': trauma_type,
                    'signature_count': len(signatures),
                    'average_severity': avg_severity,
                    'common_dimensions': common_dimensions,
                    'description': f"Recurring {trauma_type} pattern across multiple layers",
                    'significance': min(avg_severity * (len(signatures) / 3), 1.0)
                })
        
        return patterns

    def _identify_integration_opportunities(self, trauma_signatures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify integration opportunities for trauma signatures.

        Args:
            trauma_signatures: List of trauma signatures

        Returns:
            List of integration opportunities
        """
        if not trauma_signatures:
            return []
        
        opportunities = []
        
        # Look for related signatures
        for i, sig1 in enumerate(trauma_signatures):
            for j, sig2 in enumerate(trauma_signatures[i+1:], i+1):
                # Check for related dimensions
                dimensions1 = set(sig1.get('affected_dimensions', []))
                dimensions2 = set(sig2.get('affected_dimensions', []))
                
                common_dimensions = dimensions1.intersection(dimensions2)
                
                if common_dimensions:
                    opportunities.append({
                        'opportunity_id': str(uuid.uuid4()),
                        'signature_ids': [sig1.get('signature_id'), sig2.get('signature_id')],
                        'common_dimensions': list(common_dimensions),
                        'integration_approach': 'dimensional_synthesis',
                        'description': f"Integrate related patterns in {', '.join(common_dimensions)} dimensions",
                        'potential_benefit': 0.7
                    })
        
        return opportunities