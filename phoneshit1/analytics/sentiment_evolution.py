"""
Sentiment Evolution Module - Fine-Grained Sentiment Tracking

This module provides:
- Sentiment progression over time
- Emotional volatility scoring
- Sentiment shift detection
- Participant sentiment comparison
- Mood trigger identification
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import from existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages, build_contact_database
from ethics import load_ethics_config, assess_contact_from_deep_analysis, ensure_user_consent


class SentimentAnalyzer:
    """Analyzes sentiment progression and emotional patterns."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.sentiment_lexicon = self._build_sentiment_lexicon()
        
    def _build_sentiment_lexicon(self) -> Dict[str, float]:
        """Build sentiment scoring lexicon."""
        # Positive words
        positive = {
            'love': 1.0, 'loved': 1.0, 'loving': 1.0, 'adore': 1.0, 'amazing': 0.9,
            'awesome': 0.9, 'great': 0.8, 'good': 0.7, 'happy': 0.9, 'excited': 0.9,
            'wonderful': 0.9, 'fantastic': 0.9, 'excellent': 0.8, 'perfect': 0.9,
            'best': 0.8, 'beautiful': 0.8, 'lovely': 0.8, 'glad': 0.7, 'nice': 0.6,
            'thanks': 0.6, 'thank': 0.6, 'appreciate': 0.7, 'grateful': 0.8,
            'fun': 0.7, 'enjoy': 0.7, 'enjoyed': 0.7, 'laugh': 0.7, 'lol': 0.5,
            'haha': 0.5, 'yes': 0.3, 'yay': 0.7, 'congrats': 0.8, 'proud': 0.8
        }
        
        # Negative words
        negative = {
            'hate': -1.0, 'hated': -1.0, 'hating': -1.0, 'angry': -0.9, 'mad': -0.9,
            'upset': -0.8, 'sad': -0.8, 'depressed': -1.0, 'terrible': -0.9,
            'awful': -0.9, 'horrible': -0.9, 'bad': -0.7, 'worst': -0.9,
            'annoyed': -0.7, 'frustrated': -0.8, 'disappointed': -0.8,
            'hurt': -0.8, 'pain': -0.7, 'crying': -0.8, 'cry': -0.7,
            'sorry': -0.3, 'apologize': -0.3, 'mistake': -0.5, 'wrong': -0.5,
            'fight': -0.8, 'argue': -0.8, 'argument': -0.7, 'conflict': -0.7,
            'break': -0.6, 'breakup': -1.0, 'broke': -0.7, 'end': -0.6,
            'no': -0.2, 'not': -0.3, 'never': -0.4, 'nothing': -0.5
        }
        
        # Combine
        lexicon = {**positive, **negative}
        return lexicon
    
    def _calculate_message_sentiment(self, message: str) -> float:
        """Calculate sentiment score for a single message."""
        if pd.isna(message):
            return 0.0
        
        words = str(message).lower().split()
        scores = [self.sentiment_lexicon.get(word, 0.0) for word in words]
        
        if not scores:
            return 0.0
        
        # Average sentiment
        return np.mean(scores)
    
    def analyze_sentiment_progression(self, contact_name: str) -> Dict:
        """Track sentiment changes over time."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 50:
            return {'error': 'Insufficient data for sentiment analysis'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # Calculate sentiment for each message
        contact_df['sentiment'] = contact_df['message'].apply(self._calculate_message_sentiment)
        contact_df['is_outgoing'] = contact_df['type'].str.lower() == 'outgoing'
        
        # Remove neutral messages (sentiment = 0)
        contact_df = contact_df[contact_df['sentiment'] != 0.0]
        
        if len(contact_df) < 20:
            return {'error': 'Insufficient sentiment data after filtering'}
        
        # Calculate rolling averages
        window = min(50, len(contact_df) // 10)
        contact_df['sentiment_ma'] = contact_df['sentiment'].rolling(window=window, center=True).mean()
        
        # Split into phases
        phase_count = min(4, len(contact_df) // 50)
        phase_size = len(contact_df) // phase_count
        
        phases = []
        for i in range(phase_count):
            start_idx = i * phase_size
            end_idx = (i + 1) * phase_size if i < phase_count - 1 else len(contact_df)
            phase_df = contact_df.iloc[start_idx:end_idx]
            
            phases.append({
                'phase': i + 1,
                'period': f"{phase_df['timestamp'].min().strftime('%Y-%m')} to {phase_df['timestamp'].max().strftime('%Y-%m')}",
                'avg_sentiment': round(float(phase_df['sentiment'].mean()), 3),
                'sentiment_std': round(float(phase_df['sentiment'].std()), 3),
                'positive_messages_pct': round((phase_df['sentiment'] > 0).sum() / len(phase_df) * 100, 1),
                'negative_messages_pct': round((phase_df['sentiment'] < 0).sum() / len(phase_df) * 100, 1)
            })
        
        # Calculate overall trend
        x = np.arange(len(phases))
        y = np.array([p['avg_sentiment'] for p in phases])
        
        if len(x) >= 2 and np.std(y) > 0:
            slope, _, _, _, _ = stats.linregress(x, y)
            trend = 'improving' if slope > 0.01 else 'declining' if slope < -0.01 else 'stable'
        else:
            trend = 'stable'
        
        # Overall statistics
        overall_sentiment = contact_df['sentiment'].mean()
        current_sentiment = contact_df.iloc[-min(50, len(contact_df)):]['sentiment'].mean()
        peak_sentiment = max(p['avg_sentiment'] for p in phases)
        
        return {
            'contact': contact_name,
            'overall_sentiment': {
                'mean': round(float(overall_sentiment), 3),
                'current': round(float(current_sentiment), 3),
                'peak': round(float(peak_sentiment), 3),
                'trend': trend,
                'current_vs_peak': round(float(current_sentiment - peak_sentiment), 3)
            },
            'sentiment_progression': phases,
            'analysis': self._interpret_progression(phases, trend),
            'generated_at': datetime.now().isoformat()
        }
    
    def _interpret_progression(self, phases: List[Dict], trend: str) -> str:
        """Interpret sentiment progression pattern."""
        if not phases:
            return "Insufficient data"
        
        first = phases[0]['avg_sentiment']
        last = phases[-1]['avg_sentiment']
        
        if trend == 'declining':
            return f"Sentiment declining from {first:.2f} to {last:.2f} - relationship cooling"
        elif trend == 'improving':
            return f"Sentiment improving from {first:.2f} to {last:.2f} - relationship strengthening"
        else:
            return f"Stable sentiment around {last:.2f} - consistent emotional tone"
    
    def calculate_emotional_volatility(self, contact_name: str) -> Dict:
        """Measure emotional stability/volatility."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 50:
            return {'error': 'Insufficient data'}
        
        contact_df = contact_df.sort_values('timestamp')
        contact_df['sentiment'] = contact_df['message'].apply(self._calculate_message_sentiment)
        contact_df = contact_df[contact_df['sentiment'] != 0.0]
        
        if len(contact_df) < 20:
            return {'error': 'Insufficient sentiment data'}
        
        # Calculate volatility metrics
        sentiment_std = contact_df['sentiment'].std()
        sentiment_range = contact_df['sentiment'].max() - contact_df['sentiment'].min()
        
        # Calculate swing frequency (how often sentiment changes direction)
        contact_df['sentiment_diff'] = contact_df['sentiment'].diff()
        contact_df['direction_change'] = (contact_df['sentiment_diff'] * contact_df['sentiment_diff'].shift(1)) < 0
        swing_frequency = contact_df['direction_change'].sum() / len(contact_df)
        
        # Volatility score (0-100)
        volatility_score = min(100, (sentiment_std * 100) + (swing_frequency * 50))
        
        # Classify volatility
        if volatility_score > 70:
            classification = 'HIGH'
            assessment = 'Very unstable emotions - frequent mood swings'
        elif volatility_score > 50:
            classification = 'MODERATE-HIGH'
            assessment = 'Noticeable emotional ups and downs'
        elif volatility_score > 30:
            classification = 'MODERATE'
            assessment = 'Some emotional variation - normal range'
        else:
            classification = 'LOW'
            assessment = 'Stable emotional tone - consistent mood'
        
        return {
            'contact': contact_name,
            'volatility_score': round(volatility_score, 1),
            'classification': classification,
            'assessment': assessment,
            'metrics': {
                'sentiment_std': round(float(sentiment_std), 3),
                'sentiment_range': round(float(sentiment_range), 3),
                'swing_frequency': round(float(swing_frequency), 3)
            },
            'interpretation': self._interpret_volatility(volatility_score, classification),
            'generated_at': datetime.now().isoformat()
        }
    
    def _interpret_volatility(self, score: float, classification: str) -> str:
        """Interpret what volatility means for the relationship."""
        if classification == 'HIGH':
            return "High volatility suggests turbulent relationship with frequent emotional shifts. May indicate instability or intense connection."
        elif classification in ['MODERATE-HIGH', 'MODERATE']:
            return "Moderate volatility is normal - relationships naturally have emotional ups and downs."
        else:
            return "Low volatility suggests stable, consistent emotional connection. Could indicate security or emotional distance."
    
    def detect_sentiment_shifts(self, contact_name: str) -> Dict:
        """Identify major sentiment changes."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 100:
            return {'error': 'Insufficient data for shift detection'}
        
        contact_df = contact_df.sort_values('timestamp')
        contact_df['sentiment'] = contact_df['message'].apply(self._calculate_message_sentiment)
        contact_df = contact_df[contact_df['sentiment'] != 0.0]
        
        # Calculate rolling average
        window = 30
        contact_df['sentiment_ma'] = contact_df['sentiment'].rolling(window=window, center=True).mean()
        
        # Detect significant shifts
        shifts = []
        for i in range(window, len(contact_df) - window):
            before = contact_df['sentiment_ma'].iloc[i-window:i].mean()
            after = contact_df['sentiment_ma'].iloc[i:i+window].mean()
            
            if abs(after - before) > 0.3:  # Significant shift threshold
                shift_date = contact_df.iloc[i]['timestamp']
                
                # Analyze context
                context_df = contact_df[(contact_df['timestamp'] >= shift_date - timedelta(days=7)) & 
                                       (contact_df['timestamp'] <= shift_date + timedelta(days=7))]
                
                shifts.append({
                    'date': shift_date.strftime('%Y-%m-%d'),
                    'from_sentiment': round(float(before), 3),
                    'to_sentiment': round(float(after), 3),
                    'magnitude': round(float(after - before), 3),
                    'type': 'positive_shift' if after > before else 'negative_shift',
                    'context': self._analyze_shift_context(context_df)
                })
        
        # Remove duplicate shifts (too close together)
        filtered_shifts = []
        if shifts:
            filtered_shifts.append(shifts[0])
            for shift in shifts[1:]:
                shift_date = datetime.strptime(shift['date'], '%Y-%m-%d')
                last_shift_date = datetime.strptime(filtered_shifts[-1]['date'], '%Y-%m-%d')
                
                if (shift_date - last_shift_date).days > 60:
                    filtered_shifts.append(shift)
        
        return {
            'contact': contact_name,
            'shifts_detected': len(filtered_shifts),
            'major_shifts': filtered_shifts,
            'pattern': self._analyze_shift_pattern(filtered_shifts),
            'generated_at': datetime.now().isoformat()
        }
    
    def _analyze_shift_context(self, context_df: pd.DataFrame) -> str:
        """Analyze what happened during a sentiment shift."""
        if len(context_df) < 5:
            return "Insufficient context data"
        
        messages = context_df['message'].astype(str).str.lower()
        text = ' '.join(messages)
        
        # Check for context clues
        if 'break' in text or 'end' in text or 'over' in text:
            return "Relationship discussion or ending"
        elif 'fight' in text or 'argue' in text or 'angry' in text:
            return "Conflict period"
        elif 'sorry' in text or 'apologize' in text:
            return "Reconciliation or apology"
        elif 'miss' in text or 'love' in text:
            return "Emotional expression or connection"
        else:
            return "Sentiment shift without clear trigger"
    
    def _analyze_shift_pattern(self, shifts: List[Dict]) -> str:
        """Analyze overall pattern of sentiment shifts."""
        if not shifts:
            return "No major sentiment shifts detected - stable relationship"
        
        positive_shifts = sum(1 for s in shifts if s['type'] == 'positive_shift')
        negative_shifts = sum(1 for s in shifts if s['type'] == 'negative_shift')
        
        if positive_shifts > negative_shifts * 1.5:
            return f"Generally improving pattern with {positive_shifts} positive shifts"
        elif negative_shifts > positive_shifts * 1.5:
            return f"Generally declining pattern with {negative_shifts} negative shifts"
        else:
            return f"Volatile pattern with {positive_shifts} ups and {negative_shifts} downs"
    
    def compare_participant_sentiment(self, contact_name: str) -> Dict:
        """Compare sentiment between you and the contact."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 50:
            return {'error': 'Insufficient data'}
        
        contact_df['sentiment'] = contact_df['message'].apply(self._calculate_message_sentiment)
        contact_df = contact_df[contact_df['sentiment'] != 0.0]
        
        # Separate by sender
        your_messages = contact_df[contact_df['type'].str.lower() == 'outgoing']
        their_messages = contact_df[contact_df['type'].str.lower() != 'outgoing']
        
        if len(your_messages) < 10 or len(their_messages) < 10:
            return {'error': 'Insufficient messages from one participant'}
        
        your_avg = your_messages['sentiment'].mean()
        their_avg = their_messages['sentiment'].mean()
        gap = your_avg - their_avg
        
        return {
            'contact': contact_name,
            'your_avg_sentiment': round(float(your_avg), 3),
            'their_avg_sentiment': round(float(their_avg), 3),
            'sentiment_gap': round(float(gap), 3),
            'interpretation': self._interpret_sentiment_gap(gap),
            'details': {
                'your_positive_pct': round((your_messages['sentiment'] > 0).sum() / len(your_messages) * 100, 1),
                'their_positive_pct': round((their_messages['sentiment'] > 0).sum() / len(their_messages) * 100, 1),
                'your_negative_pct': round((your_messages['sentiment'] < 0).sum() / len(your_messages) * 100, 1),
                'their_negative_pct': round((their_messages['sentiment'] < 0).sum() / len(their_messages) * 100, 1)
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def _interpret_sentiment_gap(self, gap: float) -> str:
        """Interpret sentiment disparity between participants."""
        if abs(gap) < 0.05:
            return "Similar emotional expression - well matched"
        elif gap > 0.15:
            return "You express more positive sentiment - you may be more invested emotionally"
        elif gap < -0.15:
            return "They express more positive sentiment - they may be more invested emotionally"
        elif gap > 0:
            return "You're slightly more positive - minor disparity"
        else:
            return "They're slightly more positive - minor disparity"
    
    def generate_full_sentiment_report(self, contact_name: str) -> Dict:
        """Generate comprehensive sentiment analysis report."""
        progression = self.analyze_sentiment_progression(contact_name)
        volatility = self.calculate_emotional_volatility(contact_name)
        shifts = self.detect_sentiment_shifts(contact_name)
        comparison = self.compare_participant_sentiment(contact_name)
        
        return {
            'contact': contact_name,
            'sentiment_progression': progression,
            'emotional_volatility': volatility,
            'sentiment_shifts': shifts,
            'participant_comparison': comparison,
            'generated_at': datetime.now().isoformat()
        }


def save_sentiment_report(report: Dict, output_dir: str = "outputs/sentiment"):
    """Save sentiment report to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    contact_safe = report['contact'].replace('/', '_')[:100]
    filename = f"{contact_safe}_sentiment_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filepath


def main():
    """Run sentiment analysis on all contacts."""
    ensure_user_consent()
    print("=" * 60)
    print("SENTIMENT EVOLUTION ANALYSIS")
    print("=" * 60)
    
    # Load data
    print("\nLoading message data...")
    df = load_messages()
    
    print(f"Loaded {len(df)} messages")
    
    # Build deep analyses for ethics assessment
    contact_db, chat_stats = build_contact_database(df)
    from analysis_pipeline import rebuild_all_deep_analyses as _rebuild_da  # local import
    deep_analyses = _rebuild_da(df, chat_stats)
    ethics_config = load_ethics_config()
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer(df)
    
    # Analyze top 10 contacts by message volume
    contact_counts = df["chat_session"].value_counts()
    priority_contacts = list(contact_counts.head(10).index)
    
    print("\nGenerating sentiment reports for top contacts...")
    
    for contact in priority_contacts:
        ethics_info = assess_contact_from_deep_analysis(contact, deep_analyses, ethics_config)
        print(f"\n{'='*60}")
        print(f"ANALYSIS: {contact}")
        print(f"{'='*60}")
        if ethics_info.get("detail_level") == "blocked":
            print("Ethical safeguards triggered; skipping detailed sentiment analysis.")
            continue
        
        report = analyzer.generate_full_sentiment_report(contact)
        filepath = save_sentiment_report(report)
        
        # Print summary
        prog = report.get("sentiment_progression", {}).get("overall_sentiment", {})
        if prog:
            print(
                f"\nOverall Sentiment: {prog.get('mean', 0):.3f} "
                f"(Trend: {prog.get('trend', 'unknown')})"
            )
        
        vol_block = report.get("emotional_volatility", {})
        if "volatility_score" in vol_block:
            print(
                f"Volatility: {vol_block['volatility_score']}/100 "
                f"({vol_block.get('classification', 'N/A')})"
            )
        
        comparison = report.get("participant_comparison", {})
        if "sentiment_gap" in comparison:
            print(f"Sentiment Gap: {comparison['sentiment_gap']:.3f}")
        
        print(f"\nReport saved: {filepath}")
    
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
