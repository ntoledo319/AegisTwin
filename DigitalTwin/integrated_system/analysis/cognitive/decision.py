"""
Decision analysis module for cognitive analysis.

This module provides functionality for analyzing decision-making patterns and processes
based on communication data and behavior patterns.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from collections import Counter
import re

logger = logging.getLogger(__name__)

class DecisionAnalyzer:
    """Analyzer for decision-making patterns and processes."""
    
    def __init__(self):
        """Initialize the decision analyzer."""
        self.nlp_available = False
        
        # Try to import NLP libraries
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp_available = True
            logger.info("spaCy NLP model loaded successfully")
        except:
            logger.warning("spaCy model not available for decision analysis")
        
        # Initialize decision patterns dictionary
        self.decision_patterns = {}
        
        # Initialize decision indicators
        self._initialize_decision_indicators()
    
    def _initialize_decision_indicators(self):
        """Initialize linguistic indicators for decision patterns."""
        # Words and phrases associated with different decision styles
        self.decision_style_indicators = {
            'analytical': [
                'analyze', 'consider', 'evaluate', 'assess', 'examine', 'weigh', 'compare',
                'measure', 'calculate', 'quantify', 'data', 'evidence', 'information',
                'research', 'study', 'investigate', 'logical', 'rational', 'objective'
            ],
            'intuitive': [
                'feel', 'sense', 'intuition', 'gut', 'instinct', 'impression', 'hunch',
                'perceive', 'insight', 'feeling', 'emotion', 'subjective', 'experience',
                'intuit', 'perceive', 'sense', 'impression', 'spontaneous', 'immediate'
            ],
            'deliberate': [
                'plan', 'careful', 'thorough', 'methodical', 'systematic', 'organized',
                'strategic', 'thoughtful', 'detailed', 'comprehensive', 'meticulous',
                'precise', 'exact', 'rigorous', 'structured', 'step-by-step', 'process'
            ],
            'spontaneous': [
                'quick', 'immediate', 'spontaneous', 'impulse', 'sudden', 'instant', 'rapid',
                'fast', 'swift', 'prompt', 'hasty', 'expedient', 'speedy', 'hurried',
                'rushed', 'snap', 'spur-of-the-moment', 'impromptu', 'improvised'
            ],
            'collaborative': [
                'discuss', 'consult', 'collaborate', 'team', 'group', 'together', 'consensus',
                'agreement', 'collective', 'joint', 'shared', 'mutual', 'common', 'input',
                'feedback', 'opinion', 'perspective', 'view', 'advice', 'suggestion'
            ],
            'independent': [
                'alone', 'myself', 'independent', 'individual', 'personal', 'private', 'own',
                'self', 'autonomous', 'self-reliant', 'self-sufficient', 'self-determined',
                'sole', 'single', 'unaided', 'unassisted', 'separate', 'isolated', 'detached'
            ]
        }
        
        # Decision process indicators
        self.decision_process_indicators = {
            'problem_identification': [
                'problem', 'issue', 'challenge', 'difficulty', 'obstacle', 'barrier',
                'hurdle', 'complication', 'trouble', 'dilemma', 'predicament', 'situation',
                'matter', 'concern', 'question', 'query', 'doubt', 'uncertainty', 'confusion'
            ],
            'information_gathering': [
                'information', 'data', 'facts', 'details', 'evidence', 'research', 'study',
                'investigate', 'explore', 'examine', 'search', 'find', 'discover', 'learn',
                'inquire', 'ask', 'question', 'survey', 'interview', 'collect'
            ],
            'alternative_generation': [
                'option', 'alternative', 'choice', 'possibility', 'solution', 'approach',
                'method', 'way', 'path', 'route', 'course', 'direction', 'strategy',
                'plan', 'proposal', 'suggestion', 'idea', 'concept', 'scenario', 'outcome'
            ],
            'evaluation': [
                'evaluate', 'assess', 'judge', 'appraise', 'review', 'examine', 'analyze',
                'consider', 'weigh', 'compare', 'contrast', 'measure', 'test', 'check',
                'verify', 'validate', 'confirm', 'determine', 'decide', 'conclude'
            ],
            'decision_making': [
                'decide', 'choose', 'select', 'pick', 'opt', 'determine', 'resolve',
                'settle', 'conclude', 'finalize', 'commit', 'agree', 'approve', 'accept',
                'adopt', 'embrace', 'endorse', 'support', 'back', 'favor'
            ],
            'implementation': [
                'implement', 'execute', 'carry out', 'perform', 'do', 'act', 'conduct',
                'accomplish', 'achieve', 'complete', 'finish', 'fulfill', 'realize',
                'effect', 'bring about', 'make happen', 'put into action', 'put into practice'
            ],
            'evaluation_review': [
                'review', 'evaluate', 'assess', 'appraise', 'examine', 'analyze', 'study',
                'consider', 'reflect', 'contemplate', 'ponder', 'think about', 'look back',
                'reconsider', 'reassess', 'reexamine', 'revisit', 'rethink', 'reconsider'
            ]
        }
        
        # Decision bias indicators
        self.decision_bias_indicators = {
            'confirmation_bias': [
                'confirm', 'support', 'prove', 'validate', 'verify', 'substantiate',
                'corroborate', 'back up', 'reinforce', 'strengthen', 'bolster', 'uphold',
                'maintain', 'sustain', 'affirm', 'assert', 'insist', 'claim', 'contend'
            ],
            'anchoring_bias': [
                'first', 'initial', 'original', 'starting', 'beginning', 'early', 'primary',
                'preliminary', 'introductory', 'opening', 'commence', 'initiate', 'start',
                'launch', 'embark', 'set out', 'get going', 'get started', 'kick off'
            ],
            'availability_bias': [
                'remember', 'recall', 'recollect', 'reminisce', 'remind', 'memory',
                'memorable', 'unforgettable', 'mind', 'think of', 'bring to mind',
                'come to mind', 'spring to mind', 'pop into head', 'recent', 'latest'
            ],
            'loss_aversion': [
                'lose', 'loss', 'cost', 'expense', 'price', 'payment', 'fee', 'charge',
                'risk', 'danger', 'hazard', 'threat', 'peril', 'jeopardy', 'harm',
                'damage', 'injury', 'hurt', 'pain', 'suffering'
            ],
            'overconfidence': [
                'certain', 'sure', 'confident', 'positive', 'convinced', 'definite',
                'absolute', 'undoubted', 'unquestionable', 'indisputable', 'irrefutable',
                'incontrovertible', 'undeniable', 'unarguable', 'incontestable', 'obvious'
            ],
            'status_quo_bias': [
                'same', 'unchanged', 'constant', 'consistent', 'stable', 'steady',
                'fixed', 'stationary', 'static', 'immobile', 'immovable', 'unvarying',
                'invariable', 'uniform', 'regular', 'routine', 'usual', 'normal', 'typical'
            ]
        }
    
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze decision-making patterns based on messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of decision analysis results
        """
        logger.info(f"Analyzing decision patterns from {len(messages)} messages")
        
        if not messages:
            return {"error": "No messages to analyze"}
        
        try:
            # Extract text content from messages
            texts = []
            senders = set()
            
            for message in messages:
                if 'content' in message and message['content']:
                    texts.append(str(message['content']))
                elif 'text' in message and message['text']:
                    texts.append(str(message['text']))
                
                if 'sender' in message:
                    senders.add(message['sender'])
            
            # If multiple senders, we need to analyze each separately
            if len(senders) > 1:
                # Group messages by sender
                sender_messages = {}
                for message in messages:
                    sender = message.get('sender')
                    if not sender:
                        continue
                    
                    if sender not in sender_messages:
                        sender_messages[sender] = []
                    
                    content = message.get('content') or message.get('text')
                    if content:
                        sender_messages[sender].append(str(content))
                
                # Analyze each sender
                decision_profiles = {}
                for sender, sender_texts in sender_messages.items():
                    profile = await self._analyze_texts(sender_texts)
                    decision_profiles[sender] = profile
                
                return {
                    "multiple_senders": True,
                    "decision_profiles": decision_profiles
                }
            else:
                # Single sender or unknown senders
                profile = await self._analyze_texts(texts)
                
                return {
                    "multiple_senders": False,
                    "decision_profile": profile
                }
                
        except Exception as e:
            logger.error(f"Error analyzing decision patterns: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_texts(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze decision patterns from texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of decision pattern analysis results
        """
        # Combine all texts
        combined_text = " ".join(texts).lower()
        
        # Analyze decision styles
        decision_styles = await self._analyze_decision_styles(combined_text)
        
        # Analyze decision processes
        decision_processes = await self._analyze_decision_processes(combined_text)
        
        # Analyze decision biases
        decision_biases = await self._analyze_decision_biases(combined_text)
        
        # Analyze decision complexity
        decision_complexity = await self._analyze_decision_complexity(combined_text)
        
        # Store decision patterns
        self.decision_patterns = {
            "decision_styles": decision_styles,
            "decision_processes": decision_processes,
            "decision_biases": decision_biases,
            "decision_complexity": decision_complexity
        }
        
        return {
            "decision_styles": decision_styles,
            "decision_processes": decision_processes,
            "decision_biases": decision_biases,
            "decision_complexity": decision_complexity
        }
    
    async def _analyze_decision_styles(self, text: str) -> Dict[str, Any]:
        """
        Analyze decision styles from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of decision style analysis results
        """
        # Initialize style scores
        style_scores = {style: 0.0 for style in self.decision_style_indicators.keys()}
        
        # Count style indicators in text
        for style, indicators in self.decision_style_indicators.items():
            count = 0
            for word in indicators:
                count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            style_scores[style] = count
        
        # Normalize scores
        total_count = sum(style_scores.values())
        if total_count > 0:
            for style in style_scores:
                style_scores[style] = style_scores[style] / total_count
        
        # Apply some randomness to avoid identical scores
        for style in style_scores:
            style_scores[style] = min(1.0, max(0.0, style_scores[style] + np.random.normal(0, 0.02)))
        
        # Re-normalize after adding randomness
        total = sum(style_scores.values())
        if total > 0:
            for style in style_scores:
                style_scores[style] = style_scores[style] / total
        
        # Calculate composite dimensions
        analytical_intuitive = style_scores['analytical'] - style_scores['intuitive']
        deliberate_spontaneous = style_scores['deliberate'] - style_scores['spontaneous']
        collaborative_independent = style_scores['collaborative'] - style_scores['independent']
        
        # Determine primary decision style
        primary_style = max(style_scores.items(), key=lambda x: x[1])[0]
        
        # Determine secondary decision style
        style_scores_without_primary = {k: v for k, v in style_scores.items() if k != primary_style}
        secondary_style = max(style_scores_without_primary.items(), key=lambda x: x[1])[0]
        
        return {
            'style_scores': style_scores,
            'dimensions': {
                'analytical_intuitive': float(analytical_intuitive),  # Positive = analytical, Negative = intuitive
                'deliberate_spontaneous': float(deliberate_spontaneous),  # Positive = deliberate, Negative = spontaneous
                'collaborative_independent': float(collaborative_independent)  # Positive = collaborative, Negative = independent
            },
            'primary_style': primary_style,
            'secondary_style': secondary_style
        }
    
    async def _analyze_decision_processes(self, text: str) -> Dict[str, Any]:
        """
        Analyze decision processes from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of decision process analysis results
        """
        # Initialize process scores
        process_scores = {process: 0.0 for process in self.decision_process_indicators.keys()}
        
        # Count process indicators in text
        for process, indicators in self.decision_process_indicators.items():
            count = 0
            for word in indicators:
                count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            process_scores[process] = count
        
        # Normalize scores
        total_count = sum(process_scores.values())
        if total_count > 0:
            for process in process_scores:
                process_scores[process] = process_scores[process] / total_count
        
        # Apply some randomness to avoid identical scores
        for process in process_scores:
            process_scores[process] = min(1.0, max(0.0, process_scores[process] + np.random.normal(0, 0.02)))
        
        # Re-normalize after adding randomness
        total = sum(process_scores.values())
        if total > 0:
            for process in process_scores:
                process_scores[process] = process_scores[process] / total
        
        # Determine process emphasis
        # Early stage emphasis (problem identification, information gathering)
        early_stage = process_scores['problem_identification'] + process_scores['information_gathering']
        
        # Middle stage emphasis (alternative generation, evaluation)
        middle_stage = process_scores['alternative_generation'] + process_scores['evaluation']
        
        # Late stage emphasis (decision making, implementation)
        late_stage = process_scores['decision_making'] + process_scores['implementation']
        
        # Post-decision emphasis (evaluation review)
        post_decision = process_scores['evaluation_review']
        
        # Determine process focus
        process_focus = None
        max_stage = max(early_stage, middle_stage, late_stage, post_decision)
        if max_stage == early_stage:
            process_focus = 'Problem Understanding'
        elif max_stage == middle_stage:
            process_focus = 'Option Analysis'
        elif max_stage == late_stage:
            process_focus = 'Action Orientation'
        elif max_stage == post_decision:
            process_focus = 'Reflective'
        
        # Determine process completeness
        # Check if all stages have some representation
        min_threshold = 0.05
        process_completeness = all(score >= min_threshold for score in process_scores.values())
        
        return {
            'process_scores': process_scores,
            'stage_emphasis': {
                'early_stage': float(early_stage),
                'middle_stage': float(middle_stage),
                'late_stage': float(late_stage),
                'post_decision': float(post_decision)
            },
            'process_focus': process_focus,
            'process_completeness': process_completeness
        }
    
    async def _analyze_decision_biases(self, text: str) -> Dict[str, Any]:
        """
        Analyze decision biases from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of decision bias analysis results
        """
        # Initialize bias scores
        bias_scores = {bias: 0.0 for bias in self.decision_bias_indicators.keys()}
        
        # Count bias indicators in text
        for bias, indicators in self.decision_bias_indicators.items():
            count = 0
            for word in indicators:
                count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            bias_scores[bias] = count
        
        # Normalize scores
        total_count = sum(bias_scores.values())
        if total_count > 0:
            for bias in bias_scores:
                bias_scores[bias] = bias_scores[bias] / total_count
        
        # Apply some randomness to avoid identical scores
        for bias in bias_scores:
            bias_scores[bias] = min(1.0, max(0.0, bias_scores[bias] + np.random.normal(0, 0.02)))
        
        # Re-normalize after adding randomness
        total = sum(bias_scores.values())
        if total > 0:
            for bias in bias_scores:
                bias_scores[bias] = bias_scores[bias] / total
        
        # Determine primary bias
        primary_bias = max(bias_scores.items(), key=lambda x: x[1])
        
        # Determine bias susceptibility
        # Check if any bias is particularly strong
        bias_susceptibility = 'Low'
        if primary_bias[1] > 0.3:
            bias_susceptibility = 'High'
        elif primary_bias[1] > 0.2:
            bias_susceptibility = 'Moderate'
        
        return {
            'bias_scores': bias_scores,
            'primary_bias': {
                'bias': primary_bias[0],
                'score': float(primary_bias[1])
            },
            'bias_susceptibility': bias_susceptibility
        }
    
    async def _analyze_decision_complexity(self, text: str) -> Dict[str, Any]:
        """
        Analyze decision complexity from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of decision complexity analysis results
        """
        # Analyze sentence complexity
        sentences = re.split(r'[.!?]+', text)
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate average sentence length
        avg_sentence_length = sum(len(s.split()) for s in valid_sentences) / len(valid_sentences) if valid_sentences else 0
        
        # Calculate sentence complexity (approximation based on word count)
        sentence_complexity = []
        for sentence in valid_sentences:
            words = sentence.split()
            complexity = len(words)
            sentence_complexity.append(complexity)
        
        avg_complexity = sum(sentence_complexity) / len(sentence_complexity) if sentence_complexity else 0
        
        # Count conditional statements
        conditional_count = len(re.findall(r'\b(if|unless|whether|assuming|provided that|in case|suppose|supposing|given that)\b', text))
        
        # Count comparison words
        comparison_count = len(re.findall(r'\b(compare|contrast|versus|vs|against|better|worse|more|less|greater|lesser|higher|lower|stronger|weaker)\b', text))
        
        # Count uncertainty words
        uncertainty_count = len(re.findall(r'\b(maybe|perhaps|possibly|probably|likely|unlikely|chance|probability|uncertain|unsure|doubt|questionable|ambiguous)\b', text))
        
        # Calculate decision complexity score
        complexity_factors = [
            avg_complexity / 20,  # Normalize to roughly 0-1 range
            conditional_count / (len(valid_sentences) * 0.5) if valid_sentences else 0,  # Normalize by sentence count
            comparison_count / (len(valid_sentences) * 0.5) if valid_sentences else 0,  # Normalize by sentence count
            uncertainty_count / (len(valid_sentences) * 0.5) if valid_sentences else 0  # Normalize by sentence count
        ]
        
        complexity_score = sum(complexity_factors) / len(complexity_factors)
        complexity_score = min(1.0, max(0.0, complexity_score))
        
        # Determine complexity level
        complexity_level = 'Low'
        if complexity_score > 0.7:
            complexity_level = 'High'
        elif complexity_score > 0.4:
            complexity_level = 'Moderate'
        
        return {
            'metrics': {
                'avg_sentence_length': float(avg_sentence_length),
                'avg_complexity': float(avg_complexity),
                'conditional_count': conditional_count,
                'comparison_count': comparison_count,
                'uncertainty_count': uncertainty_count
            },
            'complexity_score': float(complexity_score),
            'complexity_level': complexity_level
        }
    
    def get_decision_patterns(self) -> Dict[str, Any]:
        """
        Get the current decision pattern analysis results.
        
        Returns:
            Dictionary of decision pattern analysis results
        """
        return self.decision_patterns