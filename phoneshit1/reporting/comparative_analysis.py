"""
Comparative Analysis Module
Phase 3C - Advanced Reporting

Cross-relationship insights and benchmarking:
- Romantic vs. friendship communication differences
- Your role variation across contexts
- Success vs. failure pattern identification
- Relationship type comparisons
- Personal baseline establishment
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from collections import defaultdict
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ComparativeAnalyzer:
    """Analyzes patterns across different relationship types"""
    
    def __init__(self, data_path='DATA/raw/messages.csv', outputs_base='outputs'):
        """Initialize comparative analyzer"""
        self.df = pd.read_csv(data_path)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.outputs_base = outputs_base
        
        # Load relationship categories if available
        self.categories = self._load_categories()
    
    def _load_categories(self):
        """Load relationship categorization"""
        # Try to load from existing analysis
        categories_file = 'DATA/analysis/relationship_categories_v2.json'
        
        if os.path.exists(categories_file):
            with open(categories_file, 'r') as f:
                return json.load(f)
        
        return {
            'romantic_partner': [],
            'ex_romantic_partner': [],
            'close_friends': [],
            'family': [],
            'acquaintances': []
        }
    
    def compare_romantic_vs_friends(self):
        """Compare romantic relationships vs friendships"""
        
        romantic_contacts = self.categories.get('romantic_partner', []) + self.categories.get('ex_romantic_partner', [])
        friend_contacts = self.categories.get('close_friends', [])
        
        romantic_metrics = self._calculate_group_metrics(romantic_contacts)
        friend_metrics = self._calculate_group_metrics(friend_contacts)
        
        return {
            'analysis_type': 'Romantic vs. Friendship Comparison',
            'romantic': {
                'count': len(romantic_contacts),
                'metrics': romantic_metrics,
                'contacts': romantic_contacts
            },
            'friends': {
                'count': len(friend_contacts),
                'metrics': friend_metrics,
                'contacts': friend_contacts
            },
            'key_differences': self._identify_differences(romantic_metrics, friend_metrics),
            'insights': self._generate_comparison_insights(romantic_metrics, friend_metrics)
        }
    
    def _calculate_group_metrics(self, contacts):
        """Calculate aggregate metrics for a group of contacts"""
        
        if not contacts:
            return {}
        
        all_metrics = []
        
        for contact in contacts:
            contact_data = self.df[self.df['contact_name'] == contact]
            
            if len(contact_data) < 50:
                continue
            
            your_msgs = contact_data[contact_data['is_from_me'] == True]
            total_msgs = len(contact_data)
            
            balance = len(your_msgs) / total_msgs * 100 if total_msgs > 0 else 50
            
            duration_days = (contact_data['timestamp'].max() - contact_data['timestamp'].min()).days
            msgs_per_day = total_msgs / duration_days if duration_days > 0 else 0
            
            all_metrics.append({
                'contact': contact,
                'total_messages': total_msgs,
                'balance': balance,
                'duration_days': duration_days,
                'msgs_per_day': msgs_per_day
            })
        
        if not all_metrics:
            return {}
        
        return {
            'avg_total_messages': round(np.mean([m['total_messages'] for m in all_metrics]), 0),
            'avg_balance': round(np.mean([m['balance'] for m in all_metrics]), 1),
            'avg_duration_days': round(np.mean([m['duration_days'] for m in all_metrics]), 0),
            'avg_msgs_per_day': round(np.mean([m['msgs_per_day'] for m in all_metrics]), 2),
            'total_relationships': len(all_metrics)
        }
    
    def _identify_differences(self, romantic, friends):
        """Identify key differences between groups"""
        
        if not romantic or not friends:
            return []
        
        differences = []
        
        # Message volume comparison
        if romantic.get('avg_total_messages', 0) > friends.get('avg_total_messages', 0) * 1.5:
            differences.append({
                'metric': 'Message Volume',
                'finding': 'Romantic relationships have significantly higher message volume',
                'romantic': romantic.get('avg_total_messages', 0),
                'friends': friends.get('avg_total_messages', 0)
            })
        
        # Communication frequency
        if romantic.get('avg_msgs_per_day', 0) > friends.get('avg_msgs_per_day', 0) * 2:
            differences.append({
                'metric': 'Daily Communication',
                'finding': 'Romantic relationships have much higher daily frequency',
                'romantic': romantic.get('avg_msgs_per_day', 0),
                'friends': friends.get('avg_msgs_per_day', 0)
            })
        
        # Balance comparison
        romantic_balance_diff = abs(romantic.get('avg_balance', 50) - 50)
        friends_balance_diff = abs(friends.get('avg_balance', 50) - 50)
        
        if romantic_balance_diff > friends_balance_diff + 5:
            differences.append({
                'metric': 'Balance',
                'finding': 'Romantic relationships show more imbalance in communication',
                'romantic': romantic.get('avg_balance', 50),
                'friends': friends.get('avg_balance', 50)
            })
        
        return differences
    
    def _generate_comparison_insights(self, romantic, friends):
        """Generate insights from comparison"""
        
        insights = []
        
        if not romantic or not friends:
            return ["Insufficient data for meaningful comparison"]
        
        rom_intensity = romantic.get('avg_msgs_per_day', 0)
        friend_intensity = friends.get('avg_msgs_per_day', 0)
        
        if rom_intensity > friend_intensity * 2:
            insights.append("Your romantic relationships are significantly more communication-intensive than friendships")
        
        rom_balance = romantic.get('avg_balance', 50)
        friend_balance = friends.get('avg_balance', 50)
        
        if rom_balance > 55 and friend_balance < 55:
            insights.append("You tend to pursue more in romantic relationships compared to friendships")
        elif rom_balance < 45 and friend_balance > 45:
            insights.append("Romantic partners pursue you more, while you're more balanced with friends")
        
        return insights
    
    def analyze_role_variation(self):
        """Analyze how your communication role varies across relationships"""
        
        role_analysis = {
            'romantic': [],
            'friends': [],
            'family': []
        }
        
        for category, contacts in self.categories.items():
            if category in ['romantic_partner', 'ex_romantic_partner']:
                role_type = 'romantic'
            elif category == 'close_friends':
                role_type = 'friends'
            elif category == 'family':
                role_type = 'family'
            else:
                continue
            
            for contact in contacts:
                contact_data = self.df[self.df['contact_name'] == contact]
                
                if len(contact_data) < 50:
                    continue
                
                your_msgs = contact_data[contact_data['is_from_me'] == True]
                balance = len(your_msgs) / len(contact_data) * 100
                
                # Determine role
                if balance > 60:
                    role = 'Pursuer'
                elif balance < 40:
                    role = 'Pursued'
                else:
                    role = 'Balanced'
                
                role_analysis[role_type].append({
                    'contact': contact,
                    'balance': round(balance, 1),
                    'role': role
                })
        
        # Calculate distribution
        role_distribution = {}
        for rel_type, contacts in role_analysis.items():
            if contacts:
                roles = [c['role'] for c in contacts]
                role_distribution[rel_type] = {
                    'pursuer_pct': round(roles.count('Pursuer') / len(roles) * 100, 1),
                    'balanced_pct': round(roles.count('Balanced') / len(roles) * 100, 1),
                    'pursued_pct': round(roles.count('Pursued') / len(roles) * 100, 1)
                }
        
        return {
            'analysis_type': 'Role Variation Analysis',
            'by_relationship_type': role_analysis,
            'role_distribution': role_distribution,
            'insights': self._generate_role_insights(role_distribution)
        }
    
    def _generate_role_insights(self, distribution):
        """Generate insights about role variation"""
        
        insights = []
        
        if 'romantic' in distribution and 'friends' in distribution:
            rom_pursuer = distribution['romantic'].get('pursuer_pct', 0)
            friend_pursuer = distribution['friends'].get('pursuer_pct', 0)
            
            if rom_pursuer > friend_pursuer + 20:
                insights.append("You're significantly more likely to pursue in romantic relationships")
            elif friend_pursuer > rom_pursuer + 20:
                insights.append("You pursue more in friendships than romantic relationships")
        
        # Check consistency
        if distribution:
            all_pursuer = [v.get('pursuer_pct', 0) for v in distribution.values()]
            if np.std(all_pursuer) < 15:
                insights.append("Your communication role is consistent across relationship types")
            else:
                insights.append("Your communication role varies significantly by relationship type")
        
        return insights
    
    def identify_success_patterns(self):
        """Identify patterns in successful vs. unsuccessful relationships"""
        
        # Define success/failure based on duration and current status
        successful = []
        unsuccessful = []
        
        for contact in self.df['contact_name'].unique():
            contact_data = self.df[self.df['contact_name'] == contact]
            
            if len(contact_data) < 100:
                continue
            
            duration_days = (contact_data['timestamp'].max() - contact_data['timestamp'].min()).days
            last_contact = (self.df['timestamp'].max() - contact_data['timestamp'].max()).days
            
            your_msgs = contact_data[contact_data['is_from_me'] == True]
            balance = len(your_msgs) / len(contact_data) * 100
            
            metrics = {
                'contact': contact,
                'duration_days': duration_days,
                'total_messages': len(contact_data),
                'balance': round(balance, 1),
                'last_contact_days': last_contact
            }
            
            # Success criteria: long duration + recent contact OR very high volume
            if (duration_days > 365 and last_contact < 90) or len(contact_data) > 10000:
                successful.append(metrics)
            elif duration_days > 180 and last_contact > 180:  # Ended relationships
                unsuccessful.append(metrics)
        
        # Analyze patterns
        success_patterns = self._analyze_success_patterns(successful, unsuccessful)
        
        return {
            'analysis_type': 'Success Pattern Analysis',
            'successful_relationships': len(successful),
            'unsuccessful_relationships': len(unsuccessful),
            'success_characteristics': self._calc_group_characteristics(successful),
            'failure_characteristics': self._calc_group_characteristics(unsuccessful),
            'differentiating_factors': success_patterns
        }
    
    def _calc_group_characteristics(self, relationships):
        """Calculate characteristics of a group"""
        
        if not relationships:
            return {}
        
        return {
            'avg_duration': round(np.mean([r['duration_days'] for r in relationships]), 0),
            'avg_volume': round(np.mean([r['total_messages'] for r in relationships]), 0),
            'avg_balance': round(np.mean([r['balance'] for r in relationships]), 1),
            'balance_std': round(np.std([r['balance'] for r in relationships]), 1)
        }
    
    def _analyze_success_patterns(self, successful, unsuccessful):
        """Identify what differentiates success from failure"""
        
        patterns = []
        
        if not successful or not unsuccessful:
            return ["Insufficient data for pattern analysis"]
        
        success_balance = np.mean([r['balance'] for r in successful])
        failure_balance = np.mean([r['balance'] for r in unsuccessful])
        
        if abs(success_balance - 50) < abs(failure_balance - 50):
            patterns.append("Successful relationships tend to have more balanced communication")
        
        success_volume = np.mean([r['total_messages'] for r in successful])
        failure_volume = np.mean([r['total_messages'] for r in unsuccessful])
        
        if success_volume > failure_volume * 1.5:
            patterns.append("Higher communication volume correlates with relationship longevity")
        
        patterns.append("Consistency and mutual investment are key success factors")
        
        return patterns
    
    def generate_all_comparisons(self, output_dir='outputs/comparative_analysis'):
        """Generate all comparative analyses"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("🔄 Generating Comparative Analyses...")
        print("=" * 70)
        
        analyses = {
            'romantic_vs_friends': self.compare_romantic_vs_friends(),
            'role_variation': self.analyze_role_variation(),
            'success_patterns': self.identify_success_patterns()
        }
        
        for analysis_name, analysis_data in analyses.items():
            filename = f"{output_dir}/{analysis_name}.json"
            with open(filename, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            
            print(f"  ✅ {analysis_name.replace('_', ' ').title()}")
        
        # Master summary
        master = {
            'generated': datetime.now().isoformat(),
            'analyses_included': list(analyses.keys()),
            'all_analyses': analyses
        }
        
        with open(f"{output_dir}/MASTER_COMPARATIVE.json", 'w') as f:
            json.dump(master, f, indent=2, default=str)
        
        print(f"\n{'=' * 70}")
        print(f"✅ All comparative analyses generated")
        print(f"📁 Location: {output_dir}/")
        
        return analyses

def main():
    """Main execution"""
    analyzer = ComparativeAnalyzer()
    analyzer.generate_all_comparisons()

if __name__ == "__main__":
    main()