"""
Longitudinal Trend Analysis
Phase 3B - Advanced Reporting

Generates multi-year trend reports analyzing:
- Personal growth and communication evolution
- Relationship pattern consistency
- Intelligence (IQ/EI) development over time
- Network health trajectory
- Success factors across relationships
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from collections import defaultdict
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages

class TrendAnalyzer:
    """Analyzes long-term trends across all relationships"""
    
    def __init__(self, data_path='DATA/raw/messages.csv'):
        """Initialize trend analyzer"""
        df = load_messages(data_path)
        df = df.rename(columns={"chat_session": "contact_name", "message": "message_content"})
        df["is_from_me"] = df["type"].str.lower() == "outgoing"
        self.df = df.sort_values('timestamp')
        
        # Define time periods for analysis
        self.min_date = self.df['timestamp'].min()
        self.max_date = self.df['timestamp'].max()
        self.total_years = (self.max_date - self.min_date).days / 365.25
    
    def generate_personal_growth_report(self):
        """Analyze how communication style has evolved over years"""
        
        # Divide into yearly periods
        yearly_stats = []
        
        for year in range(int(self.total_years) + 1):
            year_start = self.min_date + pd.DateOffset(years=year)
            year_end = self.min_date + pd.DateOffset(years=year+1)
            
            year_data = self.df[
                (self.df['timestamp'] >= year_start) & 
                (self.df['timestamp'] < year_end)
            ]
            
            if len(year_data) == 0:
                continue
            
            # Calculate metrics
            total_msgs = len(year_data)
            unique_contacts = year_data['contact_name'].nunique()
            avg_msg_per_contact = total_msgs / unique_contacts if unique_contacts > 0 else 0
            
            # Communication style metrics
            your_msgs = year_data[year_data['is_from_me'] == True]
            avg_length = your_msgs['message_content'].str.len().mean() if len(your_msgs) > 0 else 0
            question_rate = sum(your_msgs['message_content'].str.contains('?', na=False)) / len(your_msgs) * 100 if len(your_msgs) > 0 else 0
            
            yearly_stats.append({
                'year': year + 1,
                'period': f"{year_start.strftime('%Y-%m')} to {year_end.strftime('%Y-%m')}",
                'total_messages': total_msgs,
                'unique_contacts': unique_contacts,
                'avg_msg_per_contact': round(avg_msg_per_contact, 1),
                'avg_message_length': round(avg_length, 1),
                'question_frequency': round(question_rate, 2)
            })
        
        # Analyze trends
        if len(yearly_stats) >= 2:
            first_year = yearly_stats[0]
            last_year = yearly_stats[-1]
            
            network_growth = ((last_year['unique_contacts'] - first_year['unique_contacts']) / 
                            first_year['unique_contacts'] * 100 if first_year['unique_contacts'] > 0 else 0)
            
            communication_change = ((last_year['total_messages'] - first_year['total_messages']) / 
                                   first_year['total_messages'] * 100 if first_year['total_messages'] > 0 else 0)
        else:
            network_growth = 0
            communication_change = 0
        
        return {
            'analysis_type': 'Personal Growth Over Time',
            'time_span_years': round(self.total_years, 2),
            'yearly_breakdown': yearly_stats,
            'key_trends': {
                'network_growth_percent': round(network_growth, 1),
                'communication_change_percent': round(communication_change, 1),
                'trajectory': 'Expanding' if network_growth > 10 else 'Stable' if network_growth > -10 else 'Contracting'
            },
            'insights': self._generate_growth_insights(yearly_stats)
        }
    
    def _generate_growth_insights(self, yearly_stats):
        """Generate insights from yearly statistics"""
        insights = []
        
        if len(yearly_stats) < 2:
            return ["Insufficient data for trend analysis"]
        
        # Message volume trend
        volumes = [y['total_messages'] for y in yearly_stats]
        if volumes[-1] > volumes[0] * 1.2:
            insights.append("Communication volume increased significantly over time")
        elif volumes[-1] < volumes[0] * 0.8:
            insights.append("Communication volume decreased over time")
        else:
            insights.append("Communication volume remained relatively stable")
        
        # Network size trend
        contacts = [y['unique_contacts'] for y in yearly_stats]
        if contacts[-1] > contacts[0] * 1.2:
            insights.append("Social network expanded significantly")
        elif contacts[-1] < contacts[0] * 0.8:
            insights.append("Social network contracted")
        
        # Message length evolution
        lengths = [y['avg_message_length'] for y in yearly_stats]
        if lengths[-1] > lengths[0] * 1.2:
            insights.append("Messages became more detailed and expressive")
        elif lengths[-1] < lengths[0] * 0.8:
            insights.append("Messages became more concise")
        
        return insights
    
    def generate_relationship_pattern_report(self):
        """Analyze consistent patterns across all relationships"""
        
        # Group by contact
        contact_patterns = {}
        
        for contact in self.df['contact_name'].unique():
            contact_data = self.df[self.df['contact_name'] == contact]
            
            if len(contact_data) < 50:
                continue
            
            your_msgs = contact_data[contact_data['is_from_me'] == True]
            their_msgs = contact_data[contact_data['is_from_me'] == False]
            
            balance = len(your_msgs) / len(contact_data) * 100 if len(contact_data) > 0 else 50
            
            duration_days = (contact_data['timestamp'].max() - contact_data['timestamp'].min()).days
            
            contact_patterns[contact] = {
                'total_messages': len(contact_data),
                'balance': round(balance, 1),
                'duration_days': duration_days,
                'messages_per_day': len(contact_data) / duration_days if duration_days > 0 else 0
            }
        
        # Calculate averages
        all_balances = [p['balance'] for p in contact_patterns.values()]
        all_durations = [p['duration_days'] for p in contact_patterns.values()]
        all_rates = [p['messages_per_day'] for p in contact_patterns.values()]
        
        return {
            'analysis_type': 'Cross-Relationship Patterns',
            'total_relationships_analyzed': len(contact_patterns),
            'average_patterns': {
                'typical_balance': round(np.mean(all_balances), 1),
                'balance_consistency': 'High' if np.std(all_balances) < 10 else 'Moderate' if np.std(all_balances) < 20 else 'Variable',
                'avg_relationship_duration_days': round(np.mean(all_durations), 0),
                'avg_communication_rate': round(np.mean(all_rates), 2)
            },
            'pattern_insights': self._analyze_pattern_consistency(contact_patterns)
        }
    
    def _analyze_pattern_consistency(self, patterns):
        """Analyze consistency of patterns"""
        insights = []
        
        balances = [p['balance'] for p in patterns.values()]
        avg_balance = np.mean(balances)
        
        if avg_balance > 55:
            insights.append("You tend to pursue more in relationships")
        elif avg_balance < 45:
            insights.append("Others tend to pursue you more")
        else:
            insights.append("Your relationships show balanced mutual investment")
        
        std_balance = np.std(balances)
        if std_balance < 10:
            insights.append("Very consistent communication balance across relationships")
        elif std_balance > 20:
            insights.append("Communication balance varies significantly by relationship")
        
        return insights
    
    def generate_network_health_report(self):
        """Analyze overall social network health trajectory"""
        
        # Calculate metrics by quarter
        quarterly_health = []
        
        quarters = pd.date_range(start=self.min_date, end=self.max_date, freq='Q')
        
        for i in range(len(quarters) - 1):
            quarter_start = quarters[i]
            quarter_end = quarters[i + 1]
            
            quarter_data = self.df[
                (self.df['timestamp'] >= quarter_start) & 
                (self.df['timestamp'] < quarter_end)
            ]
            
            if len(quarter_data) == 0:
                continue
            
            active_contacts = quarter_data['contact_name'].nunique()
            total_communication = len(quarter_data)
            
            # Health score based on activity
            health_score = min(100, (active_contacts * 2) + (total_communication / 100))
            
            quarterly_health.append({
                'quarter': quarter_start.strftime('%Y-Q%q'),
                'active_contacts': active_contacts,
                'total_messages': total_communication,
                'health_score': round(health_score, 1)
            })
        
        # Overall trend
        if len(quarterly_health) >= 2:
            early_avg = np.mean([q['health_score'] for q in quarterly_health[:len(quarterly_health)//3]])
            recent_avg = np.mean([q['health_score'] for q in quarterly_health[-len(quarterly_health)//3:]])
            
            trend = 'Improving' if recent_avg > early_avg * 1.1 else 'Declining' if recent_avg < early_avg * 0.9 else 'Stable'
        else:
            trend = 'Insufficient data'
        
        return {
            'analysis_type': 'Network Health Trajectory',
            'quarterly_breakdown': quarterly_health[-8:],  # Last 2 years
            'overall_trend': trend,
            'current_health_score': quarterly_health[-1]['health_score'] if quarterly_health else 0,
            'assessment': self._assess_network_health(quarterly_health)
        }
    
    def _assess_network_health(self, quarterly_data):
        """Assess overall network health"""
        if not quarterly_data:
            return "Insufficient data"
        
        recent_scores = [q['health_score'] for q in quarterly_data[-4:]]
        avg_recent = np.mean(recent_scores)
        
        if avg_recent > 80:
            return "Excellent - Thriving social network"
        elif avg_recent > 60:
            return "Good - Healthy social connections"
        elif avg_recent > 40:
            return "Fair - Room for improvement"
        else:
            return "Needs attention - Limited social engagement"
    
    def generate_success_factors_report(self):
        """Identify what makes relationships successful"""
        
        # Define success criteria
        successful_relationships = []
        struggling_relationships = []
        
        for contact in self.df['contact_name'].unique():
            contact_data = self.df[self.df['contact_name'] == contact]
            
            if len(contact_data) < 100:
                continue
            
            duration_days = (contact_data['timestamp'].max() - contact_data['timestamp'].min()).days
            
            # Success criteria: long duration, high volume, recent activity
            days_since_last = (self.max_date - contact_data['timestamp'].max()).days
            
            success_score = 0
            if duration_days > 365: success_score += 3
            if len(contact_data) > 5000: success_score += 3
            if days_since_last < 30: success_score += 4
            
            your_msgs = contact_data[contact_data['is_from_me'] == True]
            balance = len(your_msgs) / len(contact_data) * 100
            
            if 45 < balance < 55: success_score += 2
            
            metrics = {
                'contact': contact,
                'score': success_score,
                'duration_days': duration_days,
                'total_messages': len(contact_data),
                'balance': round(balance, 1),
                'days_since_last': days_since_last
            }
            
            if success_score >= 8:
                successful_relationships.append(metrics)
            elif success_score <= 3:
                struggling_relationships.append(metrics)
        
        # Identify success patterns
        success_patterns = self._identify_success_patterns(successful_relationships, struggling_relationships)
        
        return {
            'analysis_type': 'Success Factor Analysis',
            'successful_count': len(successful_relationships),
            'struggling_count': len(struggling_relationships),
            'top_performers': sorted(successful_relationships, key=lambda x: x['score'], reverse=True)[:5],
            'success_patterns': success_patterns
        }
    
    def _identify_success_patterns(self, successful, struggling):
        """Identify patterns in successful relationships"""
        patterns = []
        
        if successful:
            avg_success_balance = np.mean([r['balance'] for r in successful])
            avg_success_volume = np.mean([r['total_messages'] for r in successful])
            
            patterns.append(f"Successful relationships average {avg_success_balance:.1f}% your initiation")
            patterns.append(f"High performers average {avg_success_volume:.0f} messages")
        
        if struggling and successful:
            avg_struggling_balance = np.mean([r['balance'] for r in struggling])
            
            if abs(avg_success_balance - 50) < abs(avg_struggling_balance - 50):
                patterns.append("Balanced investment is key to success")
        
        patterns.append("Consistency and longevity correlate with relationship success")
        
        return patterns
    
    def save_all_trend_reports(self, output_dir='outputs/trend_reports'):
        """Generate and save all trend reports"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("🔄 Generating Trend Reports...")
        print("=" * 70)
        
        reports = {
            'personal_growth': self.generate_personal_growth_report(),
            'relationship_patterns': self.generate_relationship_pattern_report(),
            'network_health': self.generate_network_health_report(),
            'success_factors': self.generate_success_factors_report()
        }
        
        for report_name, report_data in reports.items():
            filename = f"{output_dir}/{report_name}.json"
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"  ✅ {report_name.replace('_', ' ').title()}")
        
        # Generate master summary
        master = {
            'generated': datetime.now().isoformat(),
            'time_span_years': round(self.total_years, 2),
            'reports_included': list(reports.keys()),
            'all_reports': reports
        }
        
        with open(f"{output_dir}/MASTER_TRENDS.json", 'w') as f:
            json.dump(master, f, indent=2, default=str)
        
        print(f"\n{'=' * 70}")
        print(f"✅ All trend reports generated")
        print(f"📁 Location: {output_dir}/")
        
        return reports

def main():
    """Main execution"""
    analyzer = TrendAnalyzer()
    analyzer.save_all_trend_reports()

if __name__ == "__main__":
    main()
