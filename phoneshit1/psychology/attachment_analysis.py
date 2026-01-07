"""
Attachment Analysis Module - Attachment Style Detection

This module detects attachment patterns from communication behavior:
- Anxious attachment indicators
- Avoidant attachment indicators
- Secure attachment patterns
- Disorganized attachment markers
- Relationship compatibility analysis
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Import from existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages, build_contact_database
from ethics import load_ethics_config, assess_contact_from_deep_analysis, ensure_user_consent


class AttachmentAnalyzer:
    """Analyzes attachment styles from communication patterns."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.df['is_outgoing'] = self.df['type'].str.lower() == 'outgoing'
        
    def analyze_attachment_style(self, contact_name: str = None) -> Dict:
        """Analyze attachment style for a specific contact or overall."""
        if contact_name:
            return self._analyze_relationship_specific(contact_name)
        else:
            return self._analyze_overall_style()
    
    def _analyze_overall_style(self) -> Dict:
        """Analyze your overall attachment style across all relationships."""
        # Analyze across multiple relationships
        relationships = self.df['chat_session'].unique()
        
        # Filter to significant relationships only (100+ messages)
        significant_relationships = []
        for rel in relationships:
            rel_df = self.df[self.df['chat_session'] == rel]
            if len(rel_df) >= 100:
                significant_relationships.append(rel)
        
        if len(significant_relationships) < 3:
            return {'error': 'Insufficient relationships for overall analysis'}
        
        # Collect indicators across relationships
        all_indicators = {
            'anxious_scores': [],
            'avoidant_scores': [],
            'secure_scores': [],
            'disorganized_scores': []
        }
        
        for rel in significant_relationships[:20]:  # Top 20 relationships
            indicators = self._calculate_attachment_indicators(rel)
            
            if 'error' not in indicators:
                all_indicators['anxious_scores'].append(indicators['anxious_score'])
                all_indicators['avoidant_scores'].append(indicators['avoidant_score'])
                all_indicators['secure_scores'].append(indicators['secure_score'])
                all_indicators['disorganized_scores'].append(indicators['disorganized_score'])
        
        # Calculate average scores
        avg_anxious = np.mean(all_indicators['anxious_scores']) if all_indicators['anxious_scores'] else 0
        avg_avoidant = np.mean(all_indicators['avoidant_scores']) if all_indicators['avoidant_scores'] else 0
        avg_secure = np.mean(all_indicators['secure_scores']) if all_indicators['secure_scores'] else 0
        avg_disorganized = np.mean(all_indicators['disorganized_scores']) if all_indicators['disorganized_scores'] else 0
        
        # Determine primary style
        scores = {
            'Anxious-Preoccupied': avg_anxious,
            'Avoidant-Dismissive': avg_avoidant,
            'Secure': avg_secure,
            'Disorganized-Fearful': avg_disorganized
        }
        
        primary_style = max(scores, key=scores.get)
        confidence = scores[primary_style] / 100.0
        
        # Determine if mixed
        sorted_scores = sorted(scores.values(), reverse=True)
        if sorted_scores[0] - sorted_scores[1] < 15:
            mixed = True
            secondary_style = [k for k, v in scores.items() if v == sorted_scores[1]][0]
        else:
            mixed = False
            secondary_style = None
        
        return {
            'primary_attachment_style': primary_style,
            'confidence': round(confidence, 2),
            'mixed_style': mixed,
            'secondary_style': secondary_style if mixed else None,
            'scores': {k: round(v, 1) for k, v in scores.items()},
            'relationships_analyzed': len(significant_relationships),
            'indicators': self._describe_attachment_style(primary_style),
            'recommendations': self._generate_attachment_recommendations(primary_style),
            'generated_at': datetime.now().isoformat()
        }
    
    def _analyze_relationship_specific(self, contact_name: str) -> Dict:
        """Analyze attachment style within a specific relationship."""
        indicators = self._calculate_attachment_indicators(contact_name)
        
        if 'error' in indicators:
            return indicators
        
        # Determine style
        scores = {
            'Anxious': indicators['anxious_score'],
            'Avoidant': indicators['avoidant_score'],
            'Secure': indicators['secure_score'],
            'Disorganized': indicators['disorganized_score']
        }
        
        your_style = max(scores, key=scores.get)
        
        # Infer their style (opposite patterns)
        their_style = self._infer_partner_style(indicators)
        
        # Compatibility assessment
        compatibility = self._assess_compatibility(your_style, their_style)
        
        return {
            'contact': contact_name,
            'your_style_with_them': your_style,
            'their_inferred_style': their_style,
            'style_scores': {k: round(v, 1) for k, v in scores.items()},
            'compatibility': compatibility,
            'indicators': indicators,
            'relationship_dynamics': self._analyze_dynamics(your_style, their_style),
            'recommendations': self._generate_relationship_recommendations(your_style, their_style),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_attachment_indicators(self, contact_name: str) -> Dict:
        """Calculate attachment style indicators for a relationship."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 50:
            return {'error': 'Insufficient data'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # === ANXIOUS INDICATORS ===
        
        # 1. Initiation rate (anxious = high initiation)
        contact_df['time_since_last'] = contact_df['timestamp'].diff().dt.total_seconds() / 3600
        contact_df['is_convo_start'] = contact_df['time_since_last'] > 2
        
        convo_starts = contact_df[contact_df['is_convo_start']]
        if len(convo_starts) > 0:
            your_initiation_rate = (convo_starts['is_outgoing']).sum() / len(convo_starts)
        else:
            your_initiation_rate = 0.5
        
        anxious_init = min(100, max(0, (your_initiation_rate - 0.5) * 200))
        
        # 2. Response time (anxious = fast responses)
        your_messages = contact_df[contact_df['is_outgoing']].copy()
        if len(your_messages) > 10:
            your_messages['response_time'] = your_messages['timestamp'].diff().dt.total_seconds() / 60
            your_messages = your_messages[your_messages['response_time'] < 1440]  # < 24h
            
            avg_response_time = your_messages['response_time'].median()
            anxious_response = max(0, 100 - (avg_response_time / 60 * 50))  # Fast = high score
        else:
            anxious_response = 50
        
        # 3. Reassurance seeking
        messages_text = ' '.join(contact_df[contact_df['is_outgoing']]['message'].astype(str).str.lower())
        reassurance_phrases = ['are you', 'do you still', 'are we okay', 'is everything', 'are you mad',
                              'did i do', 'are you sure', 'you promise', 'you still']
        
        reassurance_count = sum(messages_text.count(phrase) for phrase in reassurance_phrases)
        reassurance_rate = reassurance_count / len(your_messages) * 1000 if len(your_messages) > 0 else 0
        anxious_reassurance = min(100, reassurance_rate * 10)
        
        # 4. Communication frequency preference (anxious = high frequency desired)
        daily_msg_count = len(contact_df) / max((contact_df['timestamp'].max() - contact_df['timestamp'].min()).days, 1)
        anxious_frequency = min(100, daily_msg_count / 50 * 100)
        
        anxious_score = (anxious_init * 0.25 + anxious_response * 0.25 + 
                        anxious_reassurance * 0.30 + anxious_frequency * 0.20)
        
        # === AVOIDANT INDICATORS ===
        
        # 1. Low initiation
        avoidant_init = max(0, (0.5 - your_initiation_rate) * 200)
        
        # 2. Slow responses
        avoidant_response = min(100, avg_response_time / 60 * 50 if 'avg_response_time' in locals() else 50)
        
        # 3. Topic deflection (short messages, low emotional content)
        your_msg_lengths = contact_df[contact_df['is_outgoing']]['message'].astype(str).str.len()
        avg_length = your_msg_lengths.mean()
        avoidant_brevity = max(0, 100 - (avg_length / 100 * 100))
        
        # 4. Emotional guardedness (low emotional vocabulary)
        emotional_words = ['feel', 'feeling', 'emotion', 'love', 'miss', 'care', 'hurt', 'happy', 'sad']
        emotional_count = sum(messages_text.count(word) for word in emotional_words)
        emotional_rate = emotional_count / len(your_messages) * 1000 if len(your_messages) > 0 else 0
        avoidant_guardedness = max(0, 100 - emotional_rate * 2)
        
        avoidant_score = (avoidant_init * 0.25 + avoidant_response * 0.25 + 
                         avoidant_brevity * 0.25 + avoidant_guardedness * 0.25)
        
        # === SECURE INDICATORS ===
        
        # 1. Balanced initiation
        secure_init = 100 - abs(your_initiation_rate - 0.5) * 200
        
        # 2. Consistent response times
        if 'avg_response_time' in locals() and len(your_messages) > 10:
            response_consistency = 100 - min(100, your_messages['response_time'].std() / avg_response_time * 50)
        else:
            response_consistency = 50
        
        # 3. Emotional openness (moderate emotional expression)
        secure_openness = min(100, emotional_rate * 2) if emotional_rate < 50 else max(0, 100 - (emotional_rate - 50))
        
        # 4. Stable engagement
        secure_stability = 100 - anxious_frequency if anxious_frequency < 70 else anxious_frequency
        
        secure_score = (secure_init * 0.30 + response_consistency * 0.25 + 
                       secure_openness * 0.25 + secure_stability * 0.20)
        
        # === DISORGANIZED INDICATORS ===
        
        # 1. Inconsistent patterns
        disorg_inconsistency = 100 - response_consistency if 'response_consistency' in locals() else 50
        
        # 2. Mixed signals (high on both anxious and avoidant)
        if anxious_score > 60 and avoidant_score > 60:
            disorg_mixed = 90
        else:
            disorg_mixed = max(0, min(anxious_score, avoidant_score))
        
        # 3. Communication volatility
        contact_df['date'] = contact_df['timestamp'].dt.date
        daily_counts = contact_df.groupby('date').size()
        if len(daily_counts) > 7:
            volatility = daily_counts.std() / daily_counts.mean() if daily_counts.mean() > 0 else 0
            disorg_volatility = min(100, volatility * 50)
        else:
            disorg_volatility = 50
        
        disorganized_score = (disorg_inconsistency * 0.4 + disorg_mixed * 0.4 + disorg_volatility * 0.2)
        
        return {
            'anxious_score': round(anxious_score, 1),
            'avoidant_score': round(avoidant_score, 1),
            'secure_score': round(secure_score, 1),
            'disorganized_score': round(disorganized_score, 1),
            'metrics': {
                'initiation_rate': round(your_initiation_rate, 3),
                'avg_response_minutes': round(avg_response_time, 1) if 'avg_response_time' in locals() else None,
                'reassurance_seeking_per_1000': round(reassurance_rate, 2),
                'avg_message_length': round(avg_length, 1),
                'emotional_expression_per_1000': round(emotional_rate, 2),
                'daily_message_frequency': round(daily_msg_count, 1)
            }
        }
    
    def _infer_partner_style(self, indicators: Dict) -> str:
        """Infer partner's attachment style from metrics."""
        metrics = indicators.get('metrics', {})
        
        # If you initiate more, they may be avoidant
        # If you initiate less, they may be anxious
        initiation_rate = metrics.get('initiation_rate', 0.5)
        
        if initiation_rate > 0.6:
            return "Likely Avoidant (you pursue more)"
        elif initiation_rate < 0.4:
            return "Likely Anxious (they pursue more)"
        else:
            return "Likely Secure (balanced engagement)"
    
    def _assess_compatibility(self, your_style: str, their_style: str) -> Dict:
        """Assess attachment style compatibility."""
        compatibility_matrix = {
            ('Secure', 'Secure'): {'score': 95, 'assessment': 'Excellent', 'description': 'Ideal pairing - mutual security and trust'},
            ('Secure', 'Anxious'): {'score': 80, 'assessment': 'Good', 'description': 'Secure partner can provide stability for anxious partner'},
            ('Secure', 'Avoidant'): {'score': 75, 'assessment': 'Moderate', 'description': 'Secure partner can help avoidant partner open up'},
            ('Anxious', 'Anxious'): {'score': 50, 'assessment': 'Challenging', 'description': 'Both partners may amplify each others insecurities'},
            ('Anxious', 'Avoidant'): {'score': 30, 'assessment': 'Difficult', 'description': 'Classic anxious-avoidant trap - pursue-withdraw cycle'},
            ('Avoidant', 'Avoidant'): {'score': 60, 'assessment': 'Moderate', 'description': 'May maintain distance but avoid conflict'},
            ('Disorganized', 'Secure'): {'score': 70, 'assessment': 'Moderate', 'description': 'Secure partner can provide grounding'},
        }
        
        key = (your_style.replace('-Preoccupied', '').replace('-Dismissive', '').replace('-Fearful', ''),
               their_style.split()[1] if 'Likely' in their_style else their_style)
        
        # Try to find match
        for combo, result in compatibility_matrix.items():
            if (combo[0] in key[0] and combo[1] in key[1]) or (combo[1] in key[0] and combo[0] in key[1]):
                return result
        
        return {'score': 50, 'assessment': 'Unknown', 'description': 'Unable to assess compatibility'}
    
    def _analyze_dynamics(self, your_style: str, their_style: str) -> str:
        """Analyze relationship dynamics based on attachment styles."""
        if 'Anxious' in your_style and 'Avoidant' in their_style:
            return "Anxious-Avoidant dynamic: You seek closeness while they seek distance, creating a pursue-withdraw pattern that can be exhausting for both."
        elif 'Avoidant' in your_style and 'Anxious' in their_style:
            return "Avoidant-Anxious dynamic: They seek reassurance while you need space, which can lead to tension and misunderstanding."
        elif 'Secure' in your_style:
            return "You bring stability to the relationship. Your secure attachment can help your partner feel safe and develop healthier patterns."
        elif 'Anxious' in your_style and 'Anxious' in their_style:
            return "Both anxious: You may amplify each other's insecurities. Focus on building individual security and trust."
        else:
            return "Your attachment dynamic requires awareness and communication to navigate successfully."
    
    def _describe_attachment_style(self, style: str) -> List[str]:
        """Describe characteristics of attachment style."""
        descriptions = {
            'Anxious-Preoccupied': [
                "Seeks high levels of intimacy and approval",
                "May worry about partner's commitment",
                "Often initiates contact and seeks reassurance",
                "Responds quickly to messages",
                "May interpret delays as rejection"
            ],
            'Avoidant-Dismissive': [
                "Values independence and self-sufficiency",
                "May feel uncomfortable with emotional intimacy",
                "Prefers maintaining emotional distance",
                "May delay responses or avoid deep conversations",
                "Emphasizes logic over emotion"
            ],
            'Secure': [
                "Comfortable with intimacy and independence",
                "Consistent and reliable in communication",
                "Expresses emotions openly but appropriately",
                "Trusts partner and feels trusted",
                "Balanced initiation and response patterns"
            ],
            'Disorganized-Fearful': [
                "Mixed feelings about closeness",
                "Inconsistent communication patterns",
                "May desire intimacy but fear vulnerability",
                "Unpredictable emotional responses",
                "Difficulty regulating emotions in relationships"
            ]
        }
        
        return descriptions.get(style, ["Style characteristics not defined"])
    
    def _generate_attachment_recommendations(self, style: str) -> List[str]:
        """Generate recommendations based on attachment style."""
        recommendations = {
            'Anxious-Preoccupied': [
                "Practice self-soothing techniques when feeling anxious about relationship",
                "Work on building self-esteem independent of partner validation",
                "Give partner space without interpreting it as rejection",
                "Communicate needs directly rather than seeking constant reassurance",
                "Consider therapy focused on attachment patterns"
            ],
            'Avoidant-Dismissive': [
                "Practice expressing emotions and vulnerability",
                "Challenge beliefs about emotional intimacy being weakness",
                "Notice when you're withdrawing and communicate your needs",
                "Work on staying present during emotional conversations",
                "Consider therapy to explore underlying fears of closeness"
            ],
            'Secure': [
                "Continue maintaining healthy boundaries and communication",
                "Use your security to model healthy attachment for partners",
                "Stay aware of partner's attachment needs",
                "Keep nurturing both intimacy and independence"
            ],
            'Disorganized-Fearful': [
                "Professional therapy strongly recommended for attachment work",
                "Practice emotional regulation techniques",
                "Work on identifying and communicating your needs",
                "Build awareness of inconsistent patterns",
                "Focus on creating safe, predictable relationship dynamics"
            ]
        }
        
        return recommendations.get(style, ["Consult with a relationship therapist for personalized guidance"])
    
    def _generate_relationship_recommendations(self, your_style: str, their_style: str) -> List[str]:
        """Generate recommendations for specific relationship dynamic."""
        if 'Anxious' in your_style and 'Avoidant' in their_style:
            return [
                "Recognize the pursue-withdraw pattern and work to break it",
                "Practice giving them space without taking it personally",
                "Communicate your need for reassurance clearly and calmly",
                "Work on self-soothing when they need distance",
                "Consider couples therapy to address this dynamic"
            ]
        elif 'Secure' in your_style:
            return [
                "Use your secure base to help partner feel safe",
                "Model healthy communication and emotional expression",
                "Be patient with their attachment patterns",
                "Encourage gradual emotional growth",
                "Maintain your own healthy boundaries"
            ]
        else:
            return [
                "Both partners should work on attachment awareness",
                "Practice clear, honest communication",
                "Consider couples counseling",
                "Read about attachment theory together",
                "Support each other's growth toward security"
            ]
    
    def generate_full_attachment_report(self, contact_name: str = None) -> Dict:
        """Generate comprehensive attachment analysis report."""
        if contact_name:
            specific = self.analyze_attachment_style(contact_name)
        else:
            specific = None
        
        overall = self._analyze_overall_style()
        
        return {
            'overall_attachment_profile': overall,
            'relationship_specific': specific,
            'generated_at': datetime.now().isoformat()
        }


def save_attachment_report(report: Dict, output_dir: str = "outputs/attachment"):
    """Save attachment report to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    
    if report.get('relationship_specific'):
        contact_safe = report['relationship_specific']['contact'].replace('/', '_')[:100]
        filename = f"{contact_safe}_attachment_{datetime.now().strftime('%Y%m%d')}.json"
    else:
        filename = f"overall_attachment_{datetime.now().strftime('%Y%m%d')}.json"
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filepath


def main():
    """Run attachment analysis."""
    ensure_user_consent()
    print("=" * 60)
    print("ATTACHMENT STYLE ANALYSIS")
    print("=" * 60)
    
    # Load data
    print("\nLoading message data...")
    df = load_messages()
    
    print(f"Loaded {len(df)} messages")
    
    # Initialize analyzer
    analyzer = AttachmentAnalyzer(df)
    ethics_config = load_ethics_config()
    
    # Overall attachment profile
    print("\n" + "="*60)
    print("YOUR OVERALL ATTACHMENT PROFILE")
    print("="*60)
    
    overall_report = analyzer.generate_full_attachment_report()
    filepath = save_attachment_report(overall_report)
    
    if 'error' not in overall_report['overall_attachment_profile']:
        profile = overall_report['overall_attachment_profile']
        print(f"\nPrimary Style: {profile['primary_attachment_style']}")
        print(f"Confidence: {profile['confidence']:.0%}")
        
        if profile['mixed_style']:
            print(f"Secondary Style: {profile['secondary_style']}")
        
        print("\nScores:")
        for style, score in profile['scores'].items():
            print(f"  {style}: {score}/100")
    
    print(f"\nReport saved: {filepath}")
    
    # Analyze specific relationships: top 6 non-system contacts by volume
    from analysis_pipeline import build_contact_database as _build_cd, rebuild_all_deep_analyses as _rebuild_da  # local imports
    _, chat_stats = _build_cd(df)
    deep_analyses = _rebuild_da(df, chat_stats)
    sorted_chats = sorted(
        (
            (name, stats.message_count)
            for name, stats in chat_stats.items()
            if stats.type != "system"
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    priority_contacts = [name for name, _ in sorted_chats[:6]]
    
    print("\n" + "="*60)
    print("RELATIONSHIP-SPECIFIC ATTACHMENT ANALYSIS")
    print("="*60)
    
    for contact in priority_contacts:
        ethics_info = assess_contact_from_deep_analysis(contact, deep_analyses, ethics_config)
        if ethics_info.get("detail_level") == "blocked":
            print(f"\n{contact}:")
            print("  Ethical safeguards triggered; skipping detailed attachment analysis.")
            continue

        if contact in df['chat_session'].unique():
            print(f"\n{contact}:")
            
            report = analyzer.generate_full_attachment_report(contact)
            filepath = save_attachment_report(report)
            
            if report['relationship_specific'] and 'error' not in report['relationship_specific']:
                rel = report['relationship_specific']
                print(f"  Your Style: {rel['your_style_with_them']}")
                print(f"  Their Style: {rel['their_inferred_style']}")
                print(f"  Compatibility: {rel['compatibility']['assessment']} ({rel['compatibility']['score']}/100)")
                print(f"  Saved: {filepath}")
    
    print("\n" + "="*60)
    print("ATTACHMENT ANALYSIS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
