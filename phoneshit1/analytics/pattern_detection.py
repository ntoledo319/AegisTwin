"""
Pattern Detection Module - Anomaly and Turning Point Analysis

This module identifies:
- Communication anomalies (gaps, spikes)
- Relationship turning points
- Recurring cycles
- Response time changes
- Initiation patterns
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import signal
from sklearn.ensemble import IsolationForest

# Import from existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages, build_contact_database
from ethics import load_ethics_config, assess_contact_from_deep_analysis, ensure_user_consent


class PatternDetector:
    """Detects anomalies and patterns in relationship communication."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def detect_anomalies(self, contact_name: str) -> Dict:
        """Identify unusual communication gaps or spikes."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 100:
            return {'error': 'Insufficient data for anomaly detection'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # Calculate daily message counts
        contact_df['date'] = contact_df['timestamp'].dt.date
        daily_counts = contact_df.groupby('date').size()
        
        # Detect gaps (days with zero messages)
        full_date_range = pd.date_range(
            start=contact_df['timestamp'].min(),
            end=contact_df['timestamp'].max(),
            freq='D'
        )
        
        gaps = []
        current_gap_start = None
        current_gap_days = 0
        
        for date in full_date_range:
            if date.date() not in daily_counts.index:
                if current_gap_start is None:
                    current_gap_start = date
                current_gap_days += 1
            else:
                if current_gap_days >= 7:  # Significant gap threshold
                    gaps.append({
                        'type': 'communication_gap',
                        'start_date': current_gap_start.strftime('%Y-%m-%d'),
                        'end_date': (current_gap_start + timedelta(days=current_gap_days-1)).strftime('%Y-%m-%d'),
                        'duration_days': current_gap_days,
                        'severity': 'critical' if current_gap_days > 30 else 'moderate' if current_gap_days > 14 else 'minor'
                    })
                current_gap_start = None
                current_gap_days = 0
        
        # Detect spikes using Isolation Forest
        if len(daily_counts) >= 30:
            X = daily_counts.values.reshape(-1, 1)
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            predictions = iso_forest.fit_predict(X)
            
            spikes = []
            for i, pred in enumerate(predictions):
                if pred == -1 and daily_counts.iloc[i] > daily_counts.median() * 2:
                    spikes.append({
                        'type': 'message_spike',
                        'date': daily_counts.index[i].strftime('%Y-%m-%d'),
                        'message_count': int(daily_counts.iloc[i]),
                        'vs_median': f"{(daily_counts.iloc[i] / daily_counts.median()):.1f}x normal"
                    })
        else:
            spikes = []
        
        return {
            'contact': contact_name,
            'anomalies_detected': len(gaps) + len(spikes),
            'communication_gaps': gaps,
            'message_spikes': spikes,
            'analysis_period': {
                'start': contact_df['timestamp'].min().strftime('%Y-%m-%d'),
                'end': contact_df['timestamp'].max().strftime('%Y-%m-%d'),
                'total_days': (contact_df['timestamp'].max() - contact_df['timestamp'].min()).days
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def identify_turning_points(self, contact_name: str) -> Dict:
        """Detect major shifts in relationship dynamics."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 200:
            return {'error': 'Insufficient data for turning point detection'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # Calculate rolling statistics
        contact_df['date'] = contact_df['timestamp'].dt.date
        daily_counts = contact_df.groupby('date').size()
        
        # Use change point detection on rolling average
        window = 30
        rolling_avg = daily_counts.rolling(window=window, center=True).mean()
        
        turning_points = []
        
        # Simple change point detection: look for significant shifts
        for i in range(window, len(rolling_avg) - window):
            before = rolling_avg.iloc[i-window:i].mean()
            after = rolling_avg.iloc[i:i+window].mean()
            
            if before > 0:
                change_pct = ((after - before) / before) * 100
                
                if abs(change_pct) > 50:  # Significant change threshold
                    # Determine type of turning point
                    if change_pct > 0:
                        tp_type = 'intensification'
                        impact = 'Relationship communication increased significantly'
                    else:
                        tp_type = 'decline'
                        impact = 'Relationship communication decreased significantly'
                    
                    # Check for contextual indicators
                    context = self._analyze_turning_point_context(
                        contact_df,
                        rolling_avg.index[i]
                    )
                    
                    turning_points.append({
                        'date': rolling_avg.index[i].strftime('%Y-%m-%d'),
                        'type': tp_type,
                        'change_percentage': round(change_pct, 1),
                        'before_avg': round(before, 1),
                        'after_avg': round(after, 1),
                        'impact': impact,
                        'context': context
                    })
        
        # Remove duplicates (turning points close together)
        filtered_turning_points = []
        if turning_points:
            filtered_turning_points.append(turning_points[0])
            for tp in turning_points[1:]:
                tp_date = datetime.strptime(tp['date'], '%Y-%m-%d')
                last_tp_date = datetime.strptime(filtered_turning_points[-1]['date'], '%Y-%m-%d')
                
                if (tp_date - last_tp_date).days > 60:  # At least 60 days apart
                    filtered_turning_points.append(tp)
        
        return {
            'contact': contact_name,
            'turning_points_detected': len(filtered_turning_points),
            'turning_points': filtered_turning_points,
            'relationship_trajectory': self._summarize_trajectory(filtered_turning_points),
            'generated_at': datetime.now().isoformat()
        }
    
    def _analyze_turning_point_context(self, df: pd.DataFrame, date: pd.Timestamp) -> str:
        """Analyze what happened around a turning point."""
        window_start = date - timedelta(days=14)
        window_end = date + timedelta(days=14)
        
        window_df = df[(df['timestamp'].dt.date >= window_start) & 
                       (df['timestamp'].dt.date <= window_end)]
        
        if len(window_df) < 10:
            return "Insufficient data for context analysis"
        
        # Check for emotional keyword changes
        messages = window_df['message'].astype(str).str.lower()
        text = ' '.join(messages)
        
        if 'love' in text or 'miss' in text:
            return "Increased emotional expression during this period"
        elif 'fight' in text or 'angry' in text or 'upset' in text:
            return "Conflict detected during this period"
        elif 'break' in text or 'end' in text:
            return "Relationship discussion during this period"
        else:
            return "Communication pattern shift"
    
    def _summarize_trajectory(self, turning_points: List[Dict]) -> str:
        """Summarize overall relationship trajectory."""
        if not turning_points:
            return "Stable relationship with no major turning points"
        
        intensifications = sum(1 for tp in turning_points if tp['type'] == 'intensification')
        declines = sum(1 for tp in turning_points if tp['type'] == 'decline')
        
        if intensifications > declines:
            return f"Overall growth trajectory with {intensifications} intensification periods"
        elif declines > intensifications:
            return f"Overall decline trajectory with {declines} decline periods"
        else:
            return f"Volatile relationship with {intensifications} ups and {declines} downs"
    
    def analyze_cycles(self, contact_name: str) -> Dict:
        """Detect recurring patterns in communication."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 100:
            return {'error': 'Insufficient data for cycle detection'}
        
        contact_df = contact_df.sort_values('timestamp')
        contact_df['date'] = contact_df['timestamp'].dt.date
        contact_df['day_of_week'] = contact_df['timestamp'].dt.dayofweek
        contact_df['hour'] = contact_df['timestamp'].dt.hour
        
        # Weekly pattern
        weekly_pattern = contact_df.groupby('day_of_week').size()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        weekly_description = []
        for day_idx, count in weekly_pattern.items():
            if day_idx < len(day_names):
                weekly_description.append(f"{day_names[day_idx]}: {count} messages")
        
        # Detect peak days
        peak_days = weekly_pattern.nlargest(2)
        peak_day_names = [day_names[i] for i in peak_days.index if i < len(day_names)]
        
        # Daily pattern
        hourly_pattern = contact_df.groupby('hour').size()
        peak_hours = hourly_pattern.nlargest(3)
        peak_hour_ranges = [f"{h}:00-{h+1}:00" for h in peak_hours.index]
        
        # Autocorrelation for periodic patterns
        daily_counts = contact_df.groupby('date').size()
        if len(daily_counts) >= 30:
            autocorr = [daily_counts.autocorr(lag=lag) for lag in range(1, min(30, len(daily_counts)))]
            
            # Find significant lags
            significant_lags = [lag+1 for lag, corr in enumerate(autocorr) if corr > 0.3]
        else:
            significant_lags = []
        
        return {
            'contact': contact_name,
            'weekly_pattern': {
                'description': weekly_description,
                'peak_days': peak_day_names,
                'pattern': 'Weekend-focused' if any(day in peak_day_names for day in ['Saturday', 'Sunday']) else 'Weekday-focused'
            },
            'daily_pattern': {
                'peak_hours': peak_hour_ranges,
                'pattern': 'Evening-focused' if any(int(h.split(':')[0]) >= 18 for h in peak_hour_ranges) else 'Daytime-focused'
            },
            'recurring_cycles': {
                'detected': len(significant_lags) > 0,
                'cycle_periods_days': significant_lags if significant_lags else [],
                'interpretation': self._interpret_cycles(significant_lags)
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def _interpret_cycles(self, lags: List[int]) -> str:
        """Interpret detected cycles."""
        if not lags:
            return "No recurring cycles detected"
        
        if 7 in lags or 6 in lags or 8 in lags:
            return "Weekly communication cycle detected"
        elif 14 in lags or 15 in lags:
            return "Bi-weekly communication pattern"
        else:
            return f"Custom cycle detected (approximately {lags[0]} days)"
    
    def track_response_times(self, contact_name: str) -> Dict:
        """Analyze how response times have changed over time."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 50:
            return {'error': 'Insufficient data for response time analysis'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # Calculate time between messages
        contact_df['time_diff_minutes'] = contact_df['timestamp'].diff().dt.total_seconds() / 60
        
        # Remove very long gaps (likely not responses)
        contact_df['time_diff_minutes'] = contact_df['time_diff_minutes'].where(
            contact_df['time_diff_minutes'] < 1440,  # 24 hours
            np.nan
        )
        
        # Split into quarters for trend analysis
        quarter_size = len(contact_df) // 4
        quarters = []
        
        for i in range(4):
            start_idx = i * quarter_size
            end_idx = (i + 1) * quarter_size if i < 3 else len(contact_df)
            quarter_df = contact_df.iloc[start_idx:end_idx]
            
            median_response = quarter_df['time_diff_minutes'].median()
            
            quarters.append({
                'quarter': i + 1,
                'median_response_minutes': round(median_response, 1) if not pd.isna(median_response) else None,
                'period': f"{quarter_df['timestamp'].min().strftime('%Y-%m')} to {quarter_df['timestamp'].max().strftime('%Y-%m')}"
            })
        
        # Calculate trend
        valid_medians = [q['median_response_minutes'] for q in quarters if q['median_response_minutes'] is not None]
        
        if len(valid_medians) >= 2:
            if valid_medians[-1] > valid_medians[0] * 1.5:
                trend = 'Slowing down - responses taking longer'
            elif valid_medians[-1] < valid_medians[0] * 0.7:
                trend = 'Speeding up - responses getting faster'
            else:
                trend = 'Stable response times'
        else:
            trend = 'Insufficient data for trend'
        
        return {
            'contact': contact_name,
            'response_time_analysis': quarters,
            'overall_trend': trend,
            'current_median_minutes': quarters[-1]['median_response_minutes'] if quarters else None,
            'interpretation': self._interpret_response_times(quarters),
            'generated_at': datetime.now().isoformat()
        }
    
    def _interpret_response_times(self, quarters: List[Dict]) -> str:
        """Interpret response time patterns."""
        if not quarters or quarters[-1]['median_response_minutes'] is None:
            return "Unable to interpret response patterns"
        
        current = quarters[-1]['median_response_minutes']
        
        if current < 15:
            return "Very fast responses - high engagement"
        elif current < 60:
            return "Quick responses - good engagement"
        elif current < 180:
            return "Moderate response time - casual engagement"
        else:
            return "Slow responses - lower engagement or busy schedules"
    
    def detect_initiation_patterns(self, contact_name: str) -> Dict:
        """Analyze who initiates conversations and when."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 50:
            return {'error': 'Insufficient data for initiation analysis'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # Define conversation start as message after 2+ hour gap
        contact_df['time_since_last'] = contact_df['timestamp'].diff().dt.total_seconds() / 3600
        contact_df['is_conversation_start'] = contact_df['time_since_last'] > 2
        
        conversation_starts = contact_df[contact_df['is_conversation_start']].copy()
        
        if len(conversation_starts) < 10:
            return {'error': 'Insufficient conversation data'}
        
        # Count who initiates
        you_initiated = (conversation_starts['type'].str.lower() == 'outgoing').sum()
        they_initiated = len(conversation_starts) - you_initiated
        
        you_pct = (you_initiated / len(conversation_starts)) * 100
        
        # Analyze timing of your initiations
        your_starts = conversation_starts[conversation_starts['type'].str.lower() == 'outgoing']
        
        if len(your_starts) > 0:
            your_starts['hour'] = your_starts['timestamp'].dt.hour
            your_starts['day_of_week'] = your_starts['timestamp'].dt.dayofweek
            
            peak_init_hours = your_starts['hour'].value_counts().head(3).index.tolist()
            peak_init_days = your_starts['day_of_week'].value_counts().head(2).index.tolist()
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            peak_days_named = [day_names[d] for d in peak_init_days if d < 7]
        else:
            peak_init_hours = []
            peak_days_named = []
        
        # Determine pattern
        if you_pct > 65:
            pattern = "You heavily pursue this relationship"
        elif you_pct > 55:
            pattern = "You initiate more often"
        elif you_pct > 45:
            pattern = "Balanced initiation"
        elif you_pct > 35:
            pattern = "They initiate more often"
        else:
            pattern = "They heavily pursue this relationship"
        
        return {
            'contact': contact_name,
            'total_conversations': len(conversation_starts),
            'you_initiated': int(you_initiated),
            'they_initiated': int(they_initiated),
            'you_initiate_percentage': round(you_pct, 1),
            'pattern': pattern,
            'your_typical_initiation_times': {
                'hours': [f"{h}:00" for h in peak_init_hours],
                'days': peak_days_named
            },
            'assessment': self._assess_initiation_balance(you_pct),
            'generated_at': datetime.now().isoformat()
        }
    
    def _assess_initiation_balance(self, you_pct: float) -> str:
        """Assess health of initiation balance."""
        if 45 <= you_pct <= 55:
            return "Healthy balanced initiation pattern"
        elif 40 <= you_pct <= 60:
            return "Slight imbalance but generally healthy"
        elif you_pct > 70:
            return "WARNING: You may be over-pursuing - consider letting them reach out more"
        elif you_pct < 30:
            return "WARNING: They may be over-pursuing - consider initiating more"
        else:
            return "Moderate imbalance - monitor this dynamic"
    
    def generate_full_pattern_report(self, contact_name: str) -> Dict:
        """Generate comprehensive pattern analysis report."""
        anomalies = self.detect_anomalies(contact_name)
        turning_points = self.identify_turning_points(contact_name)
        cycles = self.analyze_cycles(contact_name)
        response_times = self.track_response_times(contact_name)
        initiation = self.detect_initiation_patterns(contact_name)
        
        return {
            'contact': contact_name,
            'anomaly_detection': anomalies,
            'turning_points': turning_points,
            'communication_cycles': cycles,
            'response_time_analysis': response_times,
            'initiation_patterns': initiation,
            'generated_at': datetime.now().isoformat()
        }


def save_pattern_report(report: Dict, output_dir: str = "outputs/patterns"):
    """Save pattern report to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    contact_safe = report['contact'].replace('/', '_')[:100]
    filename = f"{contact_safe}_patterns_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filepath


def main():
    """Run pattern detection on all contacts."""
    ensure_user_consent()

    print("=" * 60)
    print("PATTERN DETECTION ANALYSIS")
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
    
    # Initialize detector
    detector = PatternDetector(df)
    
    # Analyze top 10 contacts by message volume
    contact_counts = df["chat_session"].value_counts()
    priority_contacts = list(contact_counts.head(10).index)
    
    print("\nGenerating pattern reports for top contacts...")
    
    for contact in priority_contacts:
        ethics_info = assess_contact_from_deep_analysis(contact, deep_analyses, ethics_config)
        print(f"\n{'='*60}")
        print(f"ANALYSIS: {contact}")
        print(f"{'='*60}")
        if ethics_info.get("detail_level") == "blocked":
            print("Ethical safeguards triggered; skipping detailed pattern analysis.")
            continue
        
        report = detector.generate_full_pattern_report(contact)
        filepath = save_pattern_report(report)
        
        # Print summary
        if "anomalies_detected" in report.get("anomaly_detection", {}):
            print(f"\nAnomalies: {report['anomaly_detection']['anomalies_detected']}")
        
        if "turning_points_detected" in report.get("turning_points", {}):
            print(f"Turning Points: {report['turning_points']['turning_points_detected']}")
        
        if "pattern" in report.get("initiation_patterns", {}):
            print(f"Initiation: {report['initiation_patterns']['pattern']}")
        
        print(f"\nReport saved: {filepath}")
    
    print("\n" + "="*60)
    print("PATTERN DETECTION COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
