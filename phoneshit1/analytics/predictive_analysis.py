"""
Predictive Analysis Module - Relationship Forecasting and Risk Assessment

This module uses machine learning and statistical analysis to:
- Forecast relationship trajectories (6-month projections)
- Calculate breakup risk scores
- Identify leading indicators and warning signs
- Compare current relationships to historical patterns
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import from existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages, build_contact_database, rebuild_all_deep_analyses
from ethics import load_ethics_config, assess_contact_from_deep_analysis, ensure_user_consent


class RelationshipPredictor:
    """Predicts relationship trajectories and assesses risk."""
    
    def __init__(self, df: pd.DataFrame, deep_analyses: Dict):
        self.df = df
        self.deep_analyses = deep_analyses
        self.historical_relationships = self._load_historical_patterns()
        
    def _load_historical_patterns(self) -> Dict:
        """Load patterns from ended relationships as training data."""
        ended_relationships = {}
        
        for name, analysis in self.deep_analyses.items():
            status = analysis.get('status', '')
            if status == 'INACTIVE' or analysis.get('days_since_last', 0) > 180:
                ended_relationships[name] = analysis
                
        return ended_relationships
    
    def _extract_features(self, contact_name: str, analysis: Dict) -> Dict:
        """Extract predictive features from relationship data."""
        phases = analysis.get('phases', [])
        
        if len(phases) < 2:
            return {}
        
        # Communication frequency features
        freq_trend = self._calculate_frequency_trend(phases)
        current_freq = phases[-1]['daily_avg'] if phases else 0
        peak_freq = max(p['daily_avg'] for p in phases) if phases else 0
        freq_decline_pct = ((peak_freq - current_freq) / peak_freq * 100) if peak_freq > 0 else 0
        
        # Balance features
        balance = analysis.get('balance', 50)
        balance_shift = self._calculate_balance_shift(contact_name)
        
        # Emotional keyword features
        emotions = analysis.get('emotional_keywords', {})
        love_ratio = emotions.get('love', 0) / analysis.get('total_messages', 1) * 1000
        conflict_ratio = emotions.get('conflict', 0) / analysis.get('total_messages', 1) * 1000
        breakup_ratio = emotions.get('breakup', 0) / analysis.get('total_messages', 1) * 1000
        reconciliation_ratio = emotions.get('reconciliation', 0) / analysis.get('total_messages', 1) * 1000
        
        # Recency features
        days_since_last = analysis.get('days_since_last', 0)
        
        # Phase volatility
        freq_volatility = self._calculate_frequency_volatility(phases)
        
        return {
            'freq_trend': freq_trend,
            'current_freq': current_freq,
            'peak_freq': peak_freq,
            'freq_decline_pct': freq_decline_pct,
            'balance': balance,
            'balance_shift': balance_shift,
            'love_ratio': love_ratio,
            'conflict_ratio': conflict_ratio,
            'breakup_ratio': breakup_ratio,
            'reconciliation_ratio': reconciliation_ratio,
            'days_since_last': days_since_last,
            'freq_volatility': freq_volatility,
            'breakup_recon_ratio': breakup_ratio / (reconciliation_ratio + 0.1)
        }
    
    def _calculate_frequency_trend(self, phases: List[Dict]) -> float:
        """Calculate linear trend in message frequency across phases."""
        if len(phases) < 2:
            return 0.0
        
        x = np.arange(len(phases))
        y = np.array([p['daily_avg'] for p in phases])
        
        if len(x) < 2 or np.std(y) == 0:
            return 0.0
        
        slope, _, _, _, _ = stats.linregress(x, y)
        return float(slope)
    
    def _calculate_balance_shift(self, contact_name: str) -> float:
        """Calculate how much message balance has shifted over time."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 100:
            return 0.0
        
        # Split into first and last quarters
        quarter_size = len(contact_df) // 4
        first_quarter = contact_df.iloc[:quarter_size]
        last_quarter = contact_df.iloc[-quarter_size:]
        
        first_balance = (first_quarter['type'].str.lower() == 'outgoing').sum() / len(first_quarter) * 100
        last_balance = (last_quarter['type'].str.lower() == 'outgoing').sum() / len(last_quarter) * 100
        
        return abs(last_balance - first_balance)
    
    def _calculate_frequency_volatility(self, phases: List[Dict]) -> float:
        """Calculate volatility in communication frequency."""
        if len(phases) < 2:
            return 0.0
        
        freqs = [p['daily_avg'] for p in phases]
        mean_freq = np.mean(freqs)
        
        if mean_freq == 0:
            return 0.0
        
        return float(np.std(freqs) / mean_freq)
    
    def calculate_breakup_risk(self, contact_name: str) -> Dict:
        """Calculate breakup risk score and identify warning signs."""
        analysis = self.deep_analyses.get(contact_name)
        
        if not analysis:
            return {'error': 'Contact not found in analysis'}
        
        features = self._extract_features(contact_name, analysis)
        
        if not features:
            return {'error': 'Insufficient data for prediction'}
        
        # Heuristic risk scoring (will be replaced with trained ML model)
        risk_score = 0
        warning_signs = []
        positive_indicators = []
        
        # Frequency decline
        if features['freq_decline_pct'] > 70:
            risk_score += 30
            warning_signs.append('severe_frequency_decline')
        elif features['freq_decline_pct'] > 50:
            risk_score += 20
            warning_signs.append('moderate_frequency_decline')
        elif features['freq_decline_pct'] < 10:
            positive_indicators.append('stable_frequency')
        
        # Negative frequency trend
        if features['freq_trend'] < -2:
            risk_score += 20
            warning_signs.append('declining_communication_trend')
        elif features['freq_trend'] > 0:
            positive_indicators.append('increasing_communication')
        
        # High breakup keywords
        if features['breakup_ratio'] > 5:
            risk_score += 25
            warning_signs.append('high_breakup_discussion')
        elif features['breakup_ratio'] < 1:
            positive_indicators.append('low_conflict_keywords')
        
        # Toxic breakup/reconciliation cycle
        if features['breakup_recon_ratio'] > 0.8 and features['breakup_ratio'] > 3:
            risk_score += 20
            warning_signs.append('toxic_breakup_reconciliation_cycle')
        
        # Imbalanced communication
        if features['balance_shift'] > 15:
            risk_score += 10
            warning_signs.append('communication_balance_shift')
        elif features['balance_shift'] < 5 and 45 < features['balance'] < 55:
            positive_indicators.append('balanced_investment')
        
        # High conflict
        if features['conflict_ratio'] > 10:
            risk_score += 15
            warning_signs.append('high_conflict_level')
        elif features['conflict_ratio'] < 3:
            positive_indicators.append('low_conflict')
        
        # Extended silence
        if features['days_since_last'] > 30:
            risk_score += 25
            warning_signs.append('extended_communication_gap')
        elif features['days_since_last'] < 7:
            positive_indicators.append('recent_active_contact')
        
        # High volatility
        if features['freq_volatility'] > 0.7:
            risk_score += 10
            warning_signs.append('unstable_communication_patterns')
        elif features['freq_volatility'] < 0.3:
            positive_indicators.append('consistent_engagement')
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Determine risk level
        if risk_score >= 75:
            risk_level = 'CRITICAL'
            assessment = 'Relationship at severe risk'
        elif risk_score >= 50:
            risk_level = 'HIGH'
            assessment = 'Significant concerns detected'
        elif risk_score >= 30:
            risk_level = 'MODERATE'
            assessment = 'Some warning signs present'
        elif risk_score >= 15:
            risk_level = 'LOW'
            assessment = 'Minor concerns, generally healthy'
        else:
            risk_level = 'VERY LOW'
            assessment = 'Relationship appears stable'
        
        return {
            'contact': contact_name,
            'risk_score': int(risk_score),
            'risk_level': risk_level,
            'assessment': assessment,
            'warning_signs': warning_signs,
            'positive_indicators': positive_indicators,
            'features_analyzed': features,
            'generated_at': datetime.now().isoformat()
        }
    
    def predict_trajectory(self, contact_name: str, months_ahead: int = 6) -> Dict:
        """Predict relationship trajectory for next N months."""
        analysis = self.deep_analyses.get(contact_name)
        
        if not analysis:
            return {'error': 'Contact not found in analysis'}
        
        features = self._extract_features(contact_name, analysis)
        risk_data = self.calculate_breakup_risk(contact_name)
        
        phases = analysis.get('phases', [])
        if not phases:
            return {'error': 'Insufficient phase data'}
        
        current_freq = phases[-1]['daily_avg']
        freq_trend = features.get('freq_trend', 0)
        
        # Project frequency for each month
        projections = []
        for month in [1, 3, 6]:
            if month > months_ahead:
                break
            
            # Simple linear projection with noise
            projected_freq = max(0, current_freq + (freq_trend * month * 30))
            
            # Adjust based on risk level
            risk_multiplier = 1.0 - (risk_data['risk_score'] / 200)  # Higher risk = steeper decline
            projected_freq *= risk_multiplier
            
            # Stability assessment
            if projected_freq > current_freq * 0.8:
                trend = 'stable' if abs(projected_freq - current_freq) < 5 else 'growing'
                prob_stable = min(0.95, 0.7 + (0.25 * (1 - risk_data['risk_score'] / 100)))
            elif projected_freq > current_freq * 0.5:
                trend = 'declining'
                prob_stable = max(0.3, 0.6 - (risk_data['risk_score'] / 150))
            else:
                trend = 'at_risk'
                prob_stable = max(0.1, 0.4 - (risk_data['risk_score'] / 100))
            
            projections.append({
                f'{month}_months': {
                    'projected_daily_frequency': round(projected_freq, 2),
                    'probability_stable': round(prob_stable, 2),
                    'trend': trend,
                    'confidence': 'moderate' if month <= 3 else 'low'
                }
            })
        
        return {
            'contact': contact_name,
            'current_frequency': round(current_freq, 2),
            'trajectory_forecast': projections,
            'risk_score': risk_data['risk_score'],
            'trend_direction': 'increasing' if freq_trend > 0 else 'declining' if freq_trend < -1 else 'stable',
            'generated_at': datetime.now().isoformat()
        }
    
    def compare_to_historical(self, contact_name: str) -> Dict:
        """Compare current relationship to historical patterns."""
        current_analysis = self.deep_analyses.get(contact_name)
        
        if not current_analysis:
            return {'error': 'Contact not found'}
        
        current_features = self._extract_features(contact_name, current_analysis)
        current_risk = self.calculate_breakup_risk(contact_name)
        
        # Compare to known ended relationships
        comparisons = []
        
        for hist_name, hist_analysis in self.historical_relationships.items():
            hist_features = self._extract_features(hist_name, hist_analysis)
            
            if not hist_features:
                continue
            
            # Calculate similarity score
            similarity = self._calculate_similarity(current_features, hist_features)
            
            comparisons.append({
                'historical_relationship': hist_name,
                'similarity_score': round(similarity, 2),
                'ended_after_days': hist_analysis.get('duration_days', 0),
                'final_breakup_count': hist_analysis.get('emotional_keywords', {}).get('breakup', 0),
                'key_differences': self._identify_differences(current_features, hist_features)
            })
        
        # Sort by similarity
        comparisons.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return {
            'contact': contact_name,
            'current_risk_score': current_risk['risk_score'],
            'most_similar_relationships': comparisons[:3],
            'pattern_analysis': self._analyze_pattern_match(current_features, comparisons),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity score between two feature sets."""
        if not features1 or not features2:
            return 0.0
        
        # Normalize and compare key features
        keys = ['freq_trend', 'freq_decline_pct', 'breakup_ratio', 'conflict_ratio', 'freq_volatility']
        
        similarities = []
        for key in keys:
            if key in features1 and key in features2:
                val1 = features1[key]
                val2 = features2[key]
                
                # Avoid division by zero
                max_val = max(abs(val1), abs(val2), 1)
                diff = abs(val1 - val2)
                sim = 1.0 - min(diff / max_val, 1.0)
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _identify_differences(self, current: Dict, historical: Dict) -> List[str]:
        """Identify key differences between current and historical relationship."""
        differences = []
        
        if current.get('freq_trend', 0) > historical.get('freq_trend', 0) + 1:
            differences.append('Current has better communication trend')
        elif current.get('freq_trend', 0) < historical.get('freq_trend', 0) - 1:
            differences.append('Current has worse communication trend')
        
        if current.get('breakup_ratio', 0) < historical.get('breakup_ratio', 0) * 0.5:
            differences.append('Much less breakup discussion')
        elif current.get('breakup_ratio', 0) > historical.get('breakup_ratio', 0) * 1.5:
            differences.append('Much more breakup discussion')
        
        if current.get('conflict_ratio', 0) < historical.get('conflict_ratio', 0) * 0.5:
            differences.append('Lower conflict level')
        elif current.get('conflict_ratio', 0) > historical.get('conflict_ratio', 0) * 1.5:
            differences.append('Higher conflict level')
        
        return differences
    
    def _analyze_pattern_match(self, current_features: Dict, comparisons: List[Dict]) -> str:
        """Analyze what the pattern matching reveals."""
        if not comparisons:
            return "No historical relationships to compare"
        
        top_match = comparisons[0]
        similarity = top_match['similarity_score']
        
        if similarity > 0.8:
            return f"STRONG similarity to {top_match['historical_relationship']} - pay attention to how that ended"
        elif similarity > 0.6:
            return f"MODERATE similarity to {top_match['historical_relationship']} - some similar patterns"
        else:
            return "Current relationship does not closely match historical patterns - unique dynamics"
    
    def generate_full_prediction_report(self, contact_name: str) -> Dict:
        """Generate comprehensive prediction report for a contact."""
        risk = self.calculate_breakup_risk(contact_name)
        trajectory = self.predict_trajectory(contact_name)
        comparison = self.compare_to_historical(contact_name)
        
        return {
            'contact': contact_name,
            'breakup_risk_assessment': risk,
            'trajectory_forecast': trajectory,
            'historical_comparison': comparison,
            'recommendations': self._generate_recommendations(risk, trajectory),
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, risk: Dict, trajectory: Dict) -> List[str]:
        """Generate personalized recommendations based on analysis."""
        recommendations = []
        
        if risk['risk_level'] in ['CRITICAL', 'HIGH']:
            recommendations.append("URGENT: This relationship needs immediate attention")
            recommendations.append("Consider having an honest conversation about the relationship status")
        
        if 'severe_frequency_decline' in risk.get('warning_signs', []):
            recommendations.append("Increase communication frequency - reach out more often")
        
        if 'high_breakup_discussion' in risk.get('warning_signs', []):
            recommendations.append("Address core relationship issues rather than repeatedly discussing breakup")
        
        if 'toxic_breakup_reconciliation_cycle' in risk.get('warning_signs', []):
            recommendations.append("CRITICAL: Break the toxic cycle - seek professional help or end relationship")
        
        if 'extended_communication_gap' in risk.get('warning_signs', []):
            recommendations.append("Re-establish contact soon or this relationship may end permanently")
        
        if trajectory.get('trend_direction') == 'declining':
            recommendations.append("Reverse the declining trend by increasing engagement quality")
        
        if not recommendations:
            recommendations.append("Relationship appears healthy - maintain current engagement")
        
        return recommendations


def save_prediction_report(report: Dict, output_dir: str = "outputs/predictions"):
    """Save prediction report to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    contact_safe = report['contact'].replace('/', '_')[:100]
    filename = f"{contact_safe}_prediction_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filepath


def main():
    """Run predictive analysis on all contacts."""
    ensure_user_consent()

    ethics_config = load_ethics_config()
    print("=" * 60)
    print("PREDICTIVE RELATIONSHIP ANALYSIS")
    print("=" * 60)
    
    # Load data
    print("\nLoading message data...")
    df = load_messages()
    contact_db, chat_stats = build_contact_database(df)
    deep_analyses = rebuild_all_deep_analyses(df, chat_stats)
    
    print(f"Loaded {len(deep_analyses)} relationships for analysis")
    
    # Initialize predictor
    predictor = RelationshipPredictor(df, deep_analyses)
    
    print(f"Identified {len(predictor.historical_relationships)} ended relationships for pattern matching")
    
    # Choose top 10 non-system contacts by message volume
    sorted_chats = sorted(
        (
            (name, stats.message_count)
            for name, stats in chat_stats.items()
            if stats.type != "system"
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    priority_contacts = [name for name, _ in sorted_chats[:10]]
    
    print("\nGenerating predictive reports for top contacts...")
    
    for contact in priority_contacts:
        ethics_info = assess_contact_from_deep_analysis(contact, deep_analyses, ethics_config)
        if ethics_info.get("detail_level") == "blocked":
            print(f"\n{'='*60}")
            print(f"ANALYSIS: {contact}")
            print(f"{'-'*60}")
            print("Ethical safeguards triggered; skipping detailed predictive analysis.")
            continue
        if contact in deep_analyses:
            print(f"\n{'='*60}")
            print(f"ANALYSIS: {contact}")
            print(f"{'='*60}")
            
            report = predictor.generate_full_prediction_report(contact)
            filepath = save_prediction_report(report)
            
            # Print summary
            risk = report['breakup_risk_assessment']
            print(f"\nRisk Score: {risk['risk_score']}/100 ({risk['risk_level']})")
            print(f"Assessment: {risk['assessment']}")
            
            if risk.get('warning_signs'):
                print(f"Warning Signs: {', '.join(risk['warning_signs'])}")
            
            if risk.get('positive_indicators'):
                print(f"Positive Indicators: {', '.join(risk['positive_indicators'])}")
            
            print(f"\nReport saved: {filepath}")
    
    print("\n" + "="*60)
    print("PREDICTIVE ANALYSIS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
