"""
Relationship Health Monitor
Phase 5A - Real-Time Monitoring

Continuous tracking of relationship health metrics:
- Daily health score updates
- Trend detection
- Baseline comparison
- Health trajectory analysis
- Early warning signals
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages

class HealthMonitor:
    """Monitors relationship health over time"""
    
    def __init__(self, data_path='DATA/raw/messages.csv'):
        """Initialize health monitor"""
        df = load_messages(data_path)
        df = df.rename(columns={"chat_session": "contact_name"})
        df["is_from_me"] = df["type"].str.lower() == "outgoing"
        self.df = df.sort_values('timestamp')
        
        # Health scoring weights
        self.weights = {
            'communication_frequency': 0.25,
            'balance': 0.20,
            'recency': 0.20,
            'trend': 0.15,
            'consistency': 0.20
        }
    
    def calculate_health_score(self, contact_name, as_of_date=None):
        """Calculate comprehensive health score for a relationship"""
        
        if as_of_date is None:
            as_of_date = self.df['timestamp'].max()
        
        contact_data = self.df[
            (self.df['contact_name'] == contact_name) & 
            (self.df['timestamp'] <= as_of_date)
        ]
        
        if len(contact_data) < 10:
            return {
                'error': 'Insufficient data',
                'health_score': 0
            }
        
        # Calculate component scores
        frequency_score = self._score_frequency(contact_data, as_of_date)
        balance_score = self._score_balance(contact_data)
        recency_score = self._score_recency(contact_data, as_of_date)
        trend_score = self._score_trend(contact_data, as_of_date)
        consistency_score = self._score_consistency(contact_data)
        
        # Calculate weighted total
        total_score = (
            frequency_score * self.weights['communication_frequency'] +
            balance_score * self.weights['balance'] +
            recency_score * self.weights['recency'] +
            trend_score * self.weights['trend'] +
            consistency_score * self.weights['consistency']
        )
        
        return {
            'contact': contact_name,
            'as_of_date': as_of_date.strftime('%Y-%m-%d'),
            'health_score': round(total_score, 1),
            'component_scores': {
                'frequency': round(frequency_score, 1),
                'balance': round(balance_score, 1),
                'recency': round(recency_score, 1),
                'trend': round(trend_score, 1),
                'consistency': round(consistency_score, 1)
            },
            'health_level': self._classify_health(total_score),
            'total_messages': len(contact_data)
        }
    
    def _score_frequency(self, contact_data, as_of_date):
        """Score communication frequency (0-100)"""
        
        # Look at last 30 days
        last_30_days = contact_data[
            contact_data['timestamp'] > (as_of_date - timedelta(days=30))
        ]
        
        if len(last_30_days) == 0:
            return 0
        
        msgs_per_day = len(last_30_days) / 30
        
        # Score based on frequency
        if msgs_per_day >= 20:
            return 100
        elif msgs_per_day >= 10:
            return 80 + (msgs_per_day - 10) * 2
        elif msgs_per_day >= 5:
            return 60 + (msgs_per_day - 5) * 4
        elif msgs_per_day >= 1:
            return 30 + (msgs_per_day - 1) * 7.5
        else:
            return msgs_per_day * 30
    
    def _score_balance(self, contact_data):
        """Score communication balance (0-100)"""
        
        your_msgs = len(contact_data[contact_data['is_from_me'] == True])
        total_msgs = len(contact_data)
        
        if total_msgs == 0:
            return 50
        
        balance_pct = (your_msgs / total_msgs) * 100
        
        # Perfect balance (50%) = 100 points
        # Deviation reduces score
        deviation = abs(balance_pct - 50)
        
        if deviation <= 5:
            return 100
        elif deviation <= 10:
            return 90 - (deviation - 5)
        elif deviation <= 20:
            return 80 - (deviation - 10) * 2
        else:
            return max(0, 60 - (deviation - 20))
    
    def _score_recency(self, contact_data, as_of_date):
        """Score how recent the last contact was (0-100)"""
        
        last_message = contact_data['timestamp'].max()
        days_since = (as_of_date - last_message).days
        
        if days_since <= 1:
            return 100
        elif days_since <= 7:
            return 90 - (days_since - 1) * 1.5
        elif days_since <= 30:
            return 70 - (days_since - 7) * 1
        elif days_since <= 90:
            return 40 - (days_since - 30) * 0.5
        else:
            return max(0, 10 - (days_since - 90) * 0.1)
    
    def _score_trend(self, contact_data, as_of_date):
        """Score communication trend (0-100)"""
        
        # Compare recent 30 days to previous 30 days
        recent_30 = contact_data[
            contact_data['timestamp'] > (as_of_date - timedelta(days=30))
        ]
        previous_30 = contact_data[
            (contact_data['timestamp'] > (as_of_date - timedelta(days=60))) &
            (contact_data['timestamp'] <= (as_of_date - timedelta(days=30)))
        ]
        
        if len(previous_30) == 0:
            return 50  # Neutral if no comparison data
        
        recent_rate = len(recent_30) / 30
        previous_rate = len(previous_30) / 30
        
        if previous_rate == 0:
            return 50
        
        change_pct = ((recent_rate - previous_rate) / previous_rate) * 100
        
        # Improving trend = higher score
        if change_pct >= 20:
            return 100
        elif change_pct >= 0:
            return 80 + change_pct
        elif change_pct >= -20:
            return 60 + change_pct
        else:
            return max(0, 40 + change_pct)
    
    def _score_consistency(self, contact_data):
        """Score consistency of communication (0-100)"""
        
        if len(contact_data) < 30:
            return 50
        
        # Calculate daily message counts
        contact_data['date'] = contact_data['timestamp'].dt.date
        daily_counts = contact_data.groupby('date').size()
        
        # Standard deviation of daily counts (lower = more consistent)
        std_dev = daily_counts.std()
        mean_msgs = daily_counts.mean()
        
        if mean_msgs == 0:
            return 50
        
        # Coefficient of variation
        cv = std_dev / mean_msgs
        
        if cv <= 0.5:
            return 100
        elif cv <= 1.0:
            return 90 - (cv - 0.5) * 20
        elif cv <= 2.0:
            return 70 - (cv - 1.0) * 20
        else:
            return max(0, 50 - (cv - 2.0) * 10)
    
    def _classify_health(self, score):
        """Classify health level"""
        
        if score >= 80:
            return "EXCELLENT"
        elif score >= 65:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        elif score >= 35:
            return "NEEDS ATTENTION"
        else:
            return "AT RISK"
    
    def track_health_over_time(self, contact_name, days_back=90):
        """Track health score changes over time"""
        
        contact_data = self.df[self.df['contact_name'] == contact_name]
        
        if len(contact_data) < 10:
            return {'error': 'Insufficient data'}
        
        end_date = contact_data['timestamp'].max()
        start_date = end_date - timedelta(days=days_back)
        
        # Calculate health at weekly intervals
        health_timeline = []
        
        current_date = start_date
        while current_date <= end_date:
            health = self.calculate_health_score(contact_name, current_date)
            
            if 'error' not in health:
                health_timeline.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'health_score': health['health_score'],
                    'health_level': health['health_level']
                })
            
            current_date += timedelta(days=7)
        
        # Analyze trajectory
        if len(health_timeline) >= 2:
            first_score = health_timeline[0]['health_score']
            last_score = health_timeline[-1]['health_score']
            change = last_score - first_score
            
            trajectory = 'Improving' if change > 5 else 'Declining' if change < -5 else 'Stable'
        else:
            trajectory = 'Unknown'
        
        return {
            'contact': contact_name,
            'period': f'{days_back} days',
            'health_timeline': health_timeline,
            'trajectory': trajectory,
            'change': round(health_timeline[-1]['health_score'] - health_timeline[0]['health_score'], 1) if health_timeline else 0
        }
    
    def monitor_all_relationships(self, min_messages=50, output_dir='outputs/health_monitoring'):
        """Monitor health of all relationships"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        contacts = self.df['contact_name'].unique()
        
        print("🔄 Monitoring Relationship Health...")
        print("=" * 70)
        
        health_report = {
            'generated': datetime.now().isoformat(),
            'total_relationships_monitored': 0,
            'health_distribution': defaultdict(int),
            'relationships': []
        }
        
        for contact in contacts:
            contact_data = self.df[self.df['contact_name'] == contact]
            
            if len(contact_data) < min_messages:
                continue
            
            health = self.calculate_health_score(contact)
            
            if 'error' not in health:
                health_report['relationships'].append(health)
                health_report['health_distribution'][health['health_level']] += 1
                health_report['total_relationships_monitored'] += 1
                
                print(f"  {contact}: {health['health_score']}/100 ({health['health_level']})")
        
        # Sort by health score
        health_report['relationships'] = sorted(
            health_report['relationships'],
            key=lambda x: x['health_score'],
            reverse=True
        )
        
        # Convert defaultdict to regular dict
        health_report['health_distribution'] = dict(health_report['health_distribution'])
        
        # Save report
        filename = f"{output_dir}/health_monitoring_report.json"
        with open(filename, 'w') as f:
            json.dump(health_report, f, indent=2, default=str)
        
        print(f"\n{'=' * 70}")
        print(f"✅ Health monitoring complete")
        print(f"📊 Distribution:")
        for level, count in sorted(health_report['health_distribution'].items()):
            print(f"  {level}: {count}")
        print(f"📁 Report saved: {filename}")
        
        return health_report
    
    def identify_at_risk_relationships(self, threshold=40):
        """Identify relationships that need attention"""
        
        at_risk = []
        
        for contact in self.df['contact_name'].unique():
            health = self.calculate_health_score(contact)
            
            if 'error' not in health and health['health_score'] < threshold:
                at_risk.append({
                    'contact': contact,
                    'health_score': health['health_score'],
                    'health_level': health['health_level'],
                    'weakest_components': self._identify_weak_components(health['component_scores'])
                })
        
        return sorted(at_risk, key=lambda x: x['health_score'])
    
    def _identify_weak_components(self, component_scores):
        """Identify which components are weakest"""
        
        weak = []
        for component, score in component_scores.items():
            if score < 50:
                weak.append(component)
        
        return weak

def main():
    """Main execution"""
    monitor = HealthMonitor()
    
    # Monitor all relationships
    report = monitor.monitor_all_relationships()
    
    # Identify at-risk relationships
    print("\n⚠️  AT-RISK RELATIONSHIPS:")
    at_risk = monitor.identify_at_risk_relationships()
    
    for rel in at_risk[:10]:
        print(f"  {rel['contact']}: {rel['health_score']}/100")
        if rel['weakest_components']:
            print(f"    Weak areas: {', '.join(rel['weakest_components'])}")

if __name__ == "__main__":
    main()
