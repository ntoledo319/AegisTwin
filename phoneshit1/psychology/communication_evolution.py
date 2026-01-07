"""
Communication Evolution Analysis Module
Phase 2B - Psychological Profiling

Tracks how communication style changes over time:
- Formality shifts (formal → casual language)
- Emotional expressiveness evolution
- Question patterns and engagement
- Listening indicators
- Style synchronization between participants
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from collections import Counter, defaultdict
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages
from ethics import ensure_user_consent

class CommunicationEvolutionAnalyzer:
    """Analyzes how communication style evolves throughout relationships"""
    
    def __init__(self, data_path='DATA/raw/messages.csv'):
        """Initialize with message data from the unified analysis pipeline."""
        df = load_messages(data_path)
        df = df.rename(columns={"chat_session": "contact_name", "message": "message_content"})
        df["is_from_me"] = df["type"].str.lower() == "outgoing"
        self.df = df
        
        # Formality indicators
        self.formal_words = {
            'please', 'thank', 'appreciate', 'regarding', 'concerning',
            'however', 'therefore', 'furthermore', 'moreover', 'indeed',
            'certainly', 'absolutely', 'precisely', 'kindly', 'sincerely'
        }
        
        self.casual_markers = {
            'lol', 'lmao', 'omg', 'wtf', 'tbh', 'ngl', 'fr', 'lowkey',
            'highkey', 'yeah', 'yup', 'nah', 'gonna', 'wanna', 'gotta',
            'haha', 'hehe', 'ugh', 'meh', 'bro', 'dude', 'yo'
        }
        
        self.intimate_markers = {
            'love', 'miss', 'care', 'feel', 'heart', 'close',
            'special', 'important', 'mean', 'appreciate', 'treasure'
        }
        
        # Emotional vocabulary
        self.emotion_words = {
            'happy', 'sad', 'angry', 'anxious', 'excited', 'nervous',
            'worried', 'stressed', 'calm', 'peaceful', 'frustrated',
            'disappointed', 'grateful', 'proud', 'ashamed', 'guilty',
            'scared', 'afraid', 'hopeful', 'optimistic', 'depressed',
            'lonely', 'overwhelmed', 'confused', 'hurt', 'upset',
            'annoyed', 'irritated', 'content', 'satisfied', 'relieved'
        }
        
        # Question types
        self.question_patterns = {
            'open': r'\b(how|why|what|when|where|who|which)\b.*\?',
            'yes_no': r'^(?!.*(how|why|what|when|where|who|which)).*\?',
            'checking_in': r'\b(you ok|doing|feeling|good|alright)\b.*\?',
            'deep': r'\b(feel|think|believe|mean|matter)\b.*\?'
        }
    
    def analyze_contact(self, contact_name):
        """Complete communication evolution analysis for a contact"""
        messages = self.df[self.df['contact_name'] == contact_name].copy()
        
        if len(messages) < 50:
            return {
                "error": "Insufficient data",
                "contact": contact_name,
                "message_count": len(messages)
            }
        
        # Sort by time
        messages = messages.sort_values('timestamp')
        
        # Divide into phases
        phases = self._divide_into_phases(messages)
        
        # Run all analyses
        results = {
            "contact": contact_name,
            "analysis_date": datetime.now().isoformat(),
            "total_messages": len(messages),
            "time_span_days": (messages['timestamp'].max() - messages['timestamp'].min()).days,
            "phases_analyzed": len(phases),
            
            "formality_evolution": self._analyze_formality_evolution(messages, phases),
            "emotional_expressiveness": self._analyze_emotional_expressiveness(messages, phases),
            "question_patterns": self._analyze_question_patterns(messages, phases),
            "listening_indicators": self._analyze_listening_indicators(messages),
            "style_synchronization": self._analyze_style_synchronization(messages),
            "vulnerability_progression": self._analyze_vulnerability_progression(messages, phases),
            "key_transitions": self._identify_key_transitions(messages, phases),
            "overall_assessment": ""
        }
        
        # Generate assessment
        results["overall_assessment"] = self._generate_assessment(results)
        
        return results
    
    def _divide_into_phases(self, messages, n_phases=4):
        """Divide relationship into temporal phases"""
        total_msgs = len(messages)
        phase_size = total_msgs // n_phases
        
        phases = []
        for i in range(n_phases):
            start_idx = i * phase_size
            end_idx = (i + 1) * phase_size if i < n_phases - 1 else total_msgs
            phases.append(messages.iloc[start_idx:end_idx])
        
        return phases
    
    def _analyze_formality_evolution(self, messages, phases):
        """Track formality changes over time"""
        evolution = []
        
        for i, phase in enumerate(phases, 1):
            formal_count = 0
            casual_count = 0
            total_words = 0
            
            for msg in phase['message_content'].dropna():
                words = msg.lower().split()
                total_words += len(words)
                
                for word in words:
                    if word in self.formal_words:
                        formal_count += 1
                    if word in self.casual_markers:
                        casual_count += 1
            
            # Calculate formality score (0-100, higher = more formal)
            if total_words > 0:
                formal_ratio = (formal_count / total_words) * 1000
                casual_ratio = (casual_count / total_words) * 1000
                formality_score = max(0, min(100, 50 + (formal_ratio - casual_ratio) * 5))
            else:
                formality_score = 50
            
            # Classify style
            if formality_score >= 70:
                style = "Formal"
            elif formality_score >= 50:
                style = "Semi-formal"
            elif formality_score >= 30:
                style = "Casual"
            else:
                style = "Very casual/intimate"
            
            evolution.append({
                "phase": i,
                "formality_score": round(formality_score, 2),
                "style": style,
                "formal_words": formal_count,
                "casual_markers": casual_count,
                "avg_message_length": round(phase['message_content'].str.len().mean(), 1)
            })
        
        # Calculate trend
        scores = [p['formality_score'] for p in evolution]
        if len(scores) >= 2:
            trend = "Becoming more casual" if scores[-1] < scores[0] else "Becoming more formal"
            change = abs(scores[-1] - scores[0])
        else:
            trend = "Stable"
            change = 0
        
        return {
            "progression": evolution,
            "trend": trend,
            "total_change": round(change, 2),
            "interpretation": self._interpret_formality_trend(evolution)
        }
    
    def _interpret_formality_trend(self, evolution):
        """Interpret what formality changes mean"""
        if len(evolution) < 2:
            return "Insufficient data"
        
        start_score = evolution[0]['formality_score']
        end_score = evolution[-1]['formality_score']
        change = end_score - start_score
        
        if change < -20:
            return "Significant casualization - relationship became much more intimate and comfortable"
        elif change < -10:
            return "Moderate casualization - growing comfort and familiarity"
        elif change > 20:
            return "Increasing formality - possible distancing or professionalization"
        elif change > 10:
            return "Moderate formalization - style becoming more careful or reserved"
        else:
            return "Stable communication style maintained throughout relationship"
    
    def _analyze_emotional_expressiveness(self, messages, phases):
        """Track emotional vocabulary evolution"""
        evolution = []
        
        for i, phase in enumerate(phases, 1):
            emotion_words_used = set()
            emotion_count = 0
            total_words = 0
            
            for msg in phase['message_content'].dropna():
                words = msg.lower().split()
                total_words += len(words)
                
                for word in words:
                    if word in self.emotion_words:
                        emotion_words_used.add(word)
                        emotion_count += 1
            
            # Calculate expressiveness metrics
            vocab_size = len(emotion_words_used)
            density = (emotion_count / total_words * 1000) if total_words > 0 else 0
            
            evolution.append({
                "phase": i,
                "unique_emotion_words": vocab_size,
                "emotion_word_density": round(density, 2),
                "total_emotion_expressions": emotion_count,
                "top_emotions": list(emotion_words_used)[:10]
            })
        
        # Calculate growth
        if len(evolution) >= 2:
            start_vocab = evolution[0]['unique_emotion_words']
            end_vocab = evolution[-1]['unique_emotion_words']
            growth = ((end_vocab - start_vocab) / max(start_vocab, 1)) * 100
        else:
            growth = 0
        
        # Assess overall level
        avg_vocab = np.mean([p['unique_emotion_words'] for p in evolution])
        if avg_vocab >= 20:
            level = "Very high"
        elif avg_vocab >= 15:
            level = "High"
        elif avg_vocab >= 10:
            level = "Moderate"
        else:
            level = "Low"
        
        return {
            "progression": evolution,
            "vocabulary_growth_percent": round(growth, 1),
            "overall_expressiveness_level": level,
            "assessment": self._assess_emotional_expressiveness(evolution, growth)
        }
    
    def _assess_emotional_expressiveness(self, evolution, growth):
        """Interpret emotional expressiveness patterns"""
        if growth > 100:
            return "Dramatic emotional opening - significant vulnerability increase over time"
        elif growth > 50:
            return "Strong emotional development - relationship deepened considerably"
        elif growth > 0:
            return "Gradual emotional opening - steady trust building"
        elif growth < -30:
            return "Emotional closing - possible withdrawal or guardedness increasing"
        else:
            return "Stable emotional expression maintained"
    
    def _analyze_question_patterns(self, messages, phases):
        """Analyze question asking patterns"""
        evolution = []
        
        for i, phase in enumerate(phases, 1):
            your_msgs = phase[phase['is_from_me'] == True]
            their_msgs = phase[phase['is_from_me'] == False]
            
            your_questions = self._count_questions_by_type(your_msgs)
            their_questions = self._count_questions_by_type(their_msgs)
            
            evolution.append({
                "phase": i,
                "your_questions": your_questions,
                "their_questions": their_questions,
                "question_balance": round(your_questions['total'] / max(their_questions['total'], 1), 2)
            })
        
        return {
            "progression": evolution,
            "interpretation": self._interpret_question_patterns(evolution)
        }
    
    def _count_questions_by_type(self, messages):
        """Count different types of questions"""
        counts = {
            'open': 0,
            'yes_no': 0,
            'checking_in': 0,
            'deep': 0,
            'total': 0
        }
        
        for msg in messages['message_content'].dropna():
            if '?' in msg:
                counts['total'] += 1
                
                for q_type, pattern in self.question_patterns.items():
                    if re.search(pattern, msg, re.IGNORECASE):
                        counts[q_type] += 1
        
        return counts
    
    def _interpret_question_patterns(self, evolution):
        """Interpret what question patterns reveal"""
        if not evolution:
            return "Insufficient data"
        
        balances = [p['question_balance'] for p in evolution]
        avg_balance = np.mean(balances)
        
        if avg_balance > 1.5:
            return "You ask significantly more questions - high curiosity/interest or potential over-pursuit"
        elif avg_balance > 1.1:
            return "You ask more questions - engaged and interested in them"
        elif avg_balance > 0.9:
            return "Balanced question exchange - mutual curiosity and engagement"
        elif avg_balance > 0.5:
            return "They ask more questions - they're more curious about you"
        else:
            return "They ask significantly more questions - they drive conversation depth"
    
    def _analyze_listening_indicators(self, messages):
        """Detect active listening signals"""
        your_msgs = messages[messages['is_from_me'] == True]
        their_msgs = messages[messages['is_from_me'] == False]
        
        # Listening indicators
        acknowledgment_words = ['yes', 'yeah', 'right', 'exactly', 'totally', 'absolutely', 'i see', 'i understand', 'that makes sense']
        followup_words = ['what', 'how', 'why', 'tell me more', 'go on', 'and then', 'really']
        empathy_words = ['sorry', 'understand', 'feel', 'imagine', 'must be', 'sounds like']
        
        your_listening_score = self._calculate_listening_score(your_msgs, acknowledgment_words, followup_words, empathy_words)
        their_listening_score = self._calculate_listening_score(their_msgs, acknowledgment_words, followup_words, empathy_words)
        
        return {
            "your_listening_score": round(your_listening_score, 2),
            "their_listening_score": round(their_listening_score, 2),
            "comparison": "You listen better" if your_listening_score > their_listening_score else "They listen better",
            "assessment": self._assess_listening(your_listening_score, their_listening_score)
        }
    
    def _calculate_listening_score(self, messages, ack_words, followup_words, empathy_words):
        """Calculate listening score from message content"""
        if len(messages) == 0:
            return 0
        
        total_score = 0
        
        for msg in messages['message_content'].dropna():
            msg_lower = msg.lower()
            
            # Check for each type of listening indicator
            for word in ack_words:
                if word in msg_lower:
                    total_score += 1
            
            for word in followup_words:
                if word in msg_lower:
                    total_score += 1.5  # Follow-up questions weighted higher
            
            for word in empathy_words:
                if word in msg_lower:
                    total_score += 2  # Empathy weighted highest
        
        # Normalize by message count
        return (total_score / len(messages)) * 10
    
    def _assess_listening(self, your_score, their_score):
        """Assess listening quality"""
        avg_score = (your_score + their_score) / 2
        
        if avg_score >= 8:
            return "Excellent mutual listening - both highly attentive and empathetic"
        elif avg_score >= 6:
            return "Good listening - generally attentive communication"
        elif avg_score >= 4:
            return "Moderate listening - some attentiveness but room for improvement"
        else:
            return "Limited listening indicators - communication may be more transactional"
    
    def _analyze_style_synchronization(self, messages):
        """Detect linguistic mirroring and style matching"""
        your_msgs = messages[messages['is_from_me'] == True]
        their_msgs = messages[messages['is_from_me'] == False]
        
        if len(your_msgs) < 10 or len(their_msgs) < 10:
            return {"error": "Insufficient data for synchronization analysis"}
        
        # Analyze various style dimensions
        your_style = self._extract_style_features(your_msgs)
        their_style = self._extract_style_features(their_msgs)
        
        # Calculate similarity across dimensions
        similarities = {}
        for key in your_style:
            if key in their_style:
                # Normalized similarity (0-1)
                diff = abs(your_style[key] - their_style[key])
                max_val = max(your_style[key], their_style[key], 1)
                similarities[key] = 1 - (diff / max_val)
        
        # Overall synchronization score
        sync_score = np.mean(list(similarities.values())) if similarities else 0
        
        return {
            "synchronization_score": round(sync_score, 3),
            "style_similarities": {k: round(v, 3) for k, v in similarities.items()},
            "your_style_profile": your_style,
            "their_style_profile": their_style,
            "interpretation": self._interpret_synchronization(sync_score)
        }
    
    def _extract_style_features(self, messages):
        """Extract communication style features"""
        features = {
            "avg_message_length": messages['message_content'].str.len().mean(),
            "avg_words_per_message": messages['message_content'].str.split().str.len().mean(),
            "punctuation_density": sum(messages['message_content'].str.count(r'[!?.]').fillna(0)) / len(messages),
            "emoji_usage": sum(messages['message_content'].str.count(r'[\U0001F600-\U0001F64F]').fillna(0)) / len(messages),
            "capitalization_rate": sum(messages['message_content'].str.isupper().fillna(False)) / len(messages)
        }
        
        return {k: round(v, 2) for k, v in features.items()}
    
    def _interpret_synchronization(self, score):
        """Interpret synchronization score"""
        if score >= 0.80:
            return "Very high synchronization - strong linguistic mirroring and rapport"
        elif score >= 0.65:
            return "High synchronization - good style matching and connection"
        elif score >= 0.50:
            return "Moderate synchronization - some style alignment"
        else:
            return "Low synchronization - distinct communication styles maintained"
    
    def _analyze_vulnerability_progression(self, messages, phases):
        """Track vulnerability and self-disclosure over time"""
        evolution = []
        
        vulnerability_markers = [
            'feel', 'scared', 'worried', 'anxious', 'afraid', 'nervous',
            'insecure', 'vulnerable', 'embarrassed', 'ashamed', 'hurt',
            'struggling', 'difficult', 'hard for me', 'admit', 'confess',
            'honest', 'truth is', 'actually', 'realize', 'understand'
        ]
        
        for i, phase in enumerate(phases, 1):
            your_msgs = phase[phase['is_from_me'] == True]
            
            vulnerability_count = 0
            for msg in your_msgs['message_content'].dropna():
                msg_lower = msg.lower()
                for marker in vulnerability_markers:
                    if marker in msg_lower:
                        vulnerability_count += 1
            
            vulnerability_rate = (vulnerability_count / len(your_msgs) * 100) if len(your_msgs) > 0 else 0
            
            evolution.append({
                "phase": i,
                "vulnerability_expressions": vulnerability_count,
                "vulnerability_rate_percent": round(vulnerability_rate, 2)
            })
        
        return {
            "progression": evolution,
            "trend": self._assess_vulnerability_trend(evolution)
        }
    
    def _assess_vulnerability_trend(self, evolution):
        """Assess vulnerability progression"""
        if len(evolution) < 2:
            return "Insufficient data"
        
        rates = [p['vulnerability_rate_percent'] for p in evolution]
        
        if rates[-1] > rates[0] * 1.5:
            return "Increasing vulnerability - growing emotional intimacy and trust"
        elif rates[-1] < rates[0] * 0.5:
            return "Decreasing vulnerability - possible emotional withdrawal or guardedness"
        else:
            return "Stable vulnerability level - consistent emotional openness"
    
    def _identify_key_transitions(self, messages, phases):
        """Identify major communication style transition points"""
        transitions = []
        
        for i in range(len(phases) - 1):
            phase1 = phases[i]
            phase2 = phases[i + 1]
            
            # Check for significant formality shift
            formal1 = self._calculate_formality_simple(phase1)
            formal2 = self._calculate_formality_simple(phase2)
            
            if abs(formal2 - formal1) > 20:
                transitions.append({
                    "between_phases": f"{i+1} and {i+2}",
                    "date": phase2['timestamp'].min().strftime('%Y-%m-%d'),
                    "change": "Formality shift",
                    "impact": "Major" if abs(formal2 - formal1) > 30 else "Moderate"
                })
        
        return transitions if transitions else [{"note": "No major style transitions detected"}]
    
    def _calculate_formality_simple(self, phase):
        """Simple formality calculation"""
        formal_count = 0
        casual_count = 0
        
        for msg in phase['message_content'].dropna():
            words = msg.lower().split()
            for word in words:
                if word in self.formal_words:
                    formal_count += 1
                if word in self.casual_markers:
                    casual_count += 1
        
        total = formal_count + casual_count
        return (formal_count / max(total, 1)) * 100
    
    def _generate_assessment(self, results):
        """Generate overall assessment"""
        assessments = []
        
        # Formality
        formality = results['formality_evolution']
        assessments.append(formality['interpretation'])
        
        # Emotional expressiveness
        emotional = results['emotional_expressiveness']
        assessments.append(emotional['assessment'])
        
        # Synchronization
        sync = results['style_synchronization']
        if 'interpretation' in sync:
            assessments.append(sync['interpretation'])
        
        return " | ".join(assessments)
    
    def save_results(self, results, output_dir='outputs/communication_evolution'):
        """Save analysis results"""
        os.makedirs(output_dir, exist_ok=True)
        
        contact = results.get('contact', 'unknown')
        filename = f"{output_dir}/{contact.replace(' ', '_')}_communication_evolution.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Communication evolution analysis saved: {filename}")
        return filename

def main():
    """Run communication evolution analysis on top contacts"""
    ensure_user_consent()
    analyzer = CommunicationEvolutionAnalyzer()
    
    # Top 10 contacts by message volume
    contact_counts = analyzer.df["contact_name"].value_counts()
    priority_contacts = list(contact_counts.head(10).index)
    
    print("🔄 Starting Communication Evolution Analysis...")
    print("=" * 70)
    
    for contact in priority_contacts:
        print(f"\n📊 Analyzing: {contact}")
        try:
            results = analyzer.analyze_contact(contact)
            
            if "error" not in results:
                analyzer.save_results(results)
                print(f"  ✓ Phases analyzed: {results['phases_analyzed']}")
                print(f"  ✓ Formality trend: {results['formality_evolution']['trend']}")
                print(f"  ✓ Emotional growth: {results['emotional_expressiveness']['vocabulary_growth_percent']}%")
                if 'synchronization_score' in results['style_synchronization']:
                    print(f"  ✓ Synchronization: {results['style_synchronization']['synchronization_score']}")
            else:
                print(f"  ⚠ {results['error']}: {results.get('message_count', 0)} messages")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Communication evolution analysis complete!")
    print(f"📁 Results saved in: outputs/communication_evolution/")

if __name__ == "__main__":
    main()
