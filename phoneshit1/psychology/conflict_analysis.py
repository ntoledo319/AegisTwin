"""
Conflict Analysis Module
Phase 2C - Psychological Profiling

Deep dive into conflict patterns and resolution strategies:
- Identify conflict periods from emotional keywords and communication patterns
- Analyze conflict triggers and common themes
- Assess resolution strategies and effectiveness
- Measure conflict recovery time
- Track conflict maturity over relationship duration
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages
from ethics import ensure_user_consent

class ConflictAnalyzer:
    """Analyzes conflict patterns, triggers, and resolution in relationships"""
    
    def __init__(self, data_path='DATA/raw/messages.csv'):
        """Initialize with message data from the unified analysis pipeline."""
        df = load_messages(data_path)
        df = df.rename(columns={"chat_session": "contact_name", "message": "message_content"})
        df["is_from_me"] = df["type"].str.lower() == "outgoing"
        self.df = df
        
        # Conflict indicators
        self.conflict_keywords = {
            'high': ['fight', 'fighting', 'angry', 'mad', 'hate', 'fuck you', 'asshole', 
                    'bitch', 'damn you', 'leave me alone', 'done', 'over', 'break up',
                    'breakup', 'breaking up', 'cant do this', 'toxic', 'abusive'],
            'medium': ['upset', 'hurt', 'disappointed', 'frustrated', 'annoyed', 'irritated',
                      'bothered', 'problem', 'issue', 'wrong', 'disagree', 'argument',
                      'arguing', 'stop', 'enough', 'tired of', 'sick of'],
            'low': ['confused', 'concerned', 'worried', 'uncomfortable', 'awkward',
                   'bothering me', 'need to talk', 'we should talk', 'discuss']
        }
        
        # Resolution indicators
        self.resolution_keywords = {
            'apology': ['sorry', 'apologize', 'my bad', 'my fault', 'shouldnt have',
                       'regret', 'forgive', 'mistake'],
            'reconciliation': ['miss you', 'love you', 'care about', 'important to me',
                             'dont want to lose', 'work it out', 'fix this', 'together'],
            'understanding': ['understand', 'see your point', 'youre right', 'makes sense',
                            'get it', 'i hear you', 'appreciate'],
            'compromise': ['okay', 'fine', 'agree', 'deal', 'fair enough', 'let me try',
                          'ill try', 'can we', 'what if']
        }
        
        # Conflict triggers
        self.trigger_keywords = {
            'commitment': ['future', 'relationship', 'serious', 'commitment', 'where is this going',
                          'what are we', 'exclusive', 'boyfriend', 'girlfriend'],
            'jealousy': ['jealous', 'who is', 'with who', 'who were you', 'talking to who',
                        'seeing someone', 'other', 'ex', 'another'],
            'communication': ['dont text', 'dont call', 'ignore', 'ignoring', 'respond',
                            'answer', 'reply', 'message me', 'talk to me'],
            'time': ['busy', 'no time', 'never have time', 'priority', 'make time',
                    'cancel', 'plans', 'hanging out with'],
            'trust': ['lie', 'lying', 'lied', 'trust', 'believe', 'honest', 'truth',
                     'hiding', 'secret'],
            'boundaries': ['space', 'alone', 'too much', 'clingy', 'needy', 'suffocating',
                          'controlling', 'privacy'],
            'respect': ['disrespect', 'rude', 'mean', 'treat me', 'deserve', 'value'],
            'money': ['money', 'pay', 'expensive', 'afford', 'cheap', 'cost', 'price'],
            'family': ['mom', 'dad', 'family', 'parents', 'sister', 'brother'],
            'plans': ['plans', 'trip', 'vacation', 'move', 'job', 'career', 'school']
        }
    
    def analyze_contact(self, contact_name):
        """Complete conflict analysis for a contact"""
        messages = self.df[self.df['contact_name'] == contact_name].copy()
        
        if len(messages) < 50:
            return {
                "error": "Insufficient data",
                "contact": contact_name,
                "message_count": len(messages)
            }
        
        messages = messages.sort_values('timestamp')
        messages['conflict_score'] = messages['message_content'].apply(self._calc_conflict_score)
        
        # Find conflict periods
        conflicts = self._find_conflicts(messages)
        
        if not conflicts:
            return {
                "contact": contact_name,
                "analysis_date": datetime.now().isoformat(),
                "conflict_profile": "LOW CONFLICT - STABLE RELATIONSHIP",
                "statistics": {"total_conflict_periods": 0, "conflict_free": True},
                "assessment": "No significant conflict patterns detected"
            }
        
        stats = self._calc_statistics(conflicts, messages)
        triggers = self._analyze_triggers(messages, conflicts)
        resolution = self._analyze_resolution(messages, conflicts)
        maturity = self._track_maturity(conflicts, messages)
        
        return {
            "contact": contact_name,
            "analysis_date": datetime.now().isoformat(),
            "total_messages": len(messages),
            "time_span_days": (messages['timestamp'].max() - messages['timestamp'].min()).days,
            "conflict_profile": self._classify_profile(stats),
            "statistics": stats,
            "top_conflicts": conflicts[:10],
            "triggers": triggers,
            "resolution_patterns": resolution,
            "conflict_maturity": maturity,
            "recommendations": self._generate_recommendations(stats, triggers, resolution, maturity)
        }
    
    def _calc_conflict_score(self, text):
        """Calculate conflict score for message"""
        if pd.isna(text):
            return 0
        text_lower = text.lower()
        score = sum(3 for w in self.conflict_keywords['high'] if w in text_lower)
        score += sum(2 for w in self.conflict_keywords['medium'] if w in text_lower)
        score += sum(1 for w in self.conflict_keywords['low'] if w in text_lower)
        return min(score, 10)
    
    def _find_conflicts(self, messages):
        """Identify conflict periods"""
        conflicts = []
        window = 15
        messages['rolling_conflict'] = messages['conflict_score'].rolling(window, min_periods=3).mean()
        
        in_conflict = False
        conflict_msgs = []
        
        for idx, row in messages.iterrows():
            if row['rolling_conflict'] >= 0.3:
                if not in_conflict:
                    in_conflict = True
                    conflict_msgs = [row]
                else:
                    conflict_msgs.append(row)
            else:
                if in_conflict and len(conflict_msgs) >= 5:
                    conflicts.append({
                        'start': conflict_msgs[0]['timestamp'],
                        'end': conflict_msgs[-1]['timestamp'],
                        'duration_days': (conflict_msgs[-1]['timestamp'] - conflict_msgs[0]['timestamp']).days,
                        'severity': np.mean([m['conflict_score'] for m in conflict_msgs]),
                        'message_count': len(conflict_msgs)
                    })
                in_conflict = False
                conflict_msgs = []
        
        return sorted(conflicts, key=lambda x: x['severity'], reverse=True)
    
    def _calc_statistics(self, conflicts, messages):
        """Calculate conflict statistics"""
        if not conflicts:
            return {}
        
        durations = [c['duration_days'] for c in conflicts]
        severities = [c['severity'] for c in conflicts]
        
        total_days = (messages['timestamp'].max() - messages['timestamp'].min()).days
        avg_interval = total_days / len(conflicts) if len(conflicts) > 1 else total_days
        
        return {
            "total_conflicts": len(conflicts),
            "avg_duration_days": round(np.mean(durations), 1),
            "max_duration_days": max(durations),
            "avg_severity": round(np.mean(severities), 2),
            "max_severity": round(max(severities), 2),
            "conflict_frequency_days": round(avg_interval, 1),
            "total_conflict_days": sum(durations)
        }
    
    def _analyze_triggers(self, messages, conflicts):
        """Identify conflict triggers"""
        trigger_counts = defaultdict(int)
        
        for conflict in conflicts[:20]:
            conflict_msgs = messages[
                (messages['timestamp'] >= conflict['start']) &
                (messages['timestamp'] <= conflict['end'])
            ]
            
            for _, msg in conflict_msgs.iterrows():
                if pd.isna(msg['message_content']):
                    continue
                text_lower = msg['message_content'].lower()
                
                for trigger, keywords in self.trigger_keywords.items():
                    if any(kw in text_lower for kw in keywords):
                        trigger_counts[trigger] += 1
        
        sorted_triggers = sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"topic": trigger, "frequency": count, "severity": "high" if count > 5 else "moderate"}
            for trigger, count in sorted_triggers[:10]
        ]
    
    def _analyze_resolution(self, messages, conflicts):
        """Analyze resolution patterns"""
        resolution_types = defaultdict(int)
        recovery_times = []
        
        for conflict in conflicts[:15]:
            # Look at messages after conflict
            post_conflict = messages[
                messages['timestamp'] > conflict['end']
            ].head(30)
            
            for _, msg in post_conflict.iterrows():
                if pd.isna(msg['message_content']):
                    continue
                text_lower = msg['message_content'].lower()
                
                for res_type, keywords in self.resolution_keywords.items():
                    if any(kw in text_lower for kw in keywords):
                        resolution_types[res_type] += 1
                        break
        
        primary = max(resolution_types.items(), key=lambda x: x[1])[0] if resolution_types else "unclear"
        
        return {
            "primary_strategy": primary,
            "resolution_breakdown": dict(resolution_types),
            "effectiveness": "moderate"
        }
    
    def _track_maturity(self, conflicts, messages):
        """Track conflict maturity over time"""
        if len(conflicts) < 4:
            return {"assessment": "Insufficient conflicts to track maturity"}
        
        mid_point = len(conflicts) // 2
        early_conflicts = conflicts[-mid_point:]
        late_conflicts = conflicts[:mid_point]
        
        early_severity = np.mean([c['severity'] for c in early_conflicts])
        late_severity = np.mean([c['severity'] for c in late_conflicts])
        
        early_duration = np.mean([c['duration_days'] for c in early_conflicts])
        late_duration = np.mean([c['duration_days'] for c in late_conflicts])
        
        if late_severity < early_severity * 0.7:
            trend = "IMPROVING"
        elif late_severity > early_severity * 1.3:
            trend = "WORSENING"
        else:
            trend = "STABLE"
        
        return {
            "early_avg_severity": round(early_severity, 2),
            "late_avg_severity": round(late_severity, 2),
            "trend": trend,
            "assessment": f"Conflict patterns are {trend.lower()}"
        }
    
    def _classify_profile(self, stats):
        """Classify conflict profile"""
        if stats['total_conflicts'] == 0:
            return "LOW CONFLICT - STABLE"
        elif stats['total_conflicts'] > 20 and stats['avg_severity'] > 5:
            return "HIGH CONFLICT - TOXIC PATTERN"
        elif stats['total_conflicts'] > 10:
            return "MODERATE-HIGH CONFLICT"
        else:
            return "LOW-MODERATE CONFLICT"
    
    def _generate_recommendations(self, stats, triggers, resolution, maturity):
        """Generate recommendations based on analysis"""
        recs = []
        
        if stats.get('total_conflicts', 0) > 15:
            recs.append("High conflict frequency suggests fundamental compatibility issues")
        
        if triggers:
            top_trigger = triggers[0]['topic']
            recs.append(f"Primary conflict trigger is {top_trigger} - address this proactively")
        
        if maturity.get('trend') == "WORSENING":
            recs.append("CRITICAL: Conflicts are escalating - consider relationship evaluation")
        elif maturity.get('trend') == "IMPROVING":
            recs.append("POSITIVE: Conflict resolution improving over time")
        
        if not recs:
            recs.append("Healthy conflict patterns detected")
        
        return recs
    
    def save_results(self, results, output_dir='outputs/conflict_analysis'):
        """Save analysis results"""
        os.makedirs(output_dir, exist_ok=True)
        contact = results.get('contact', 'unknown')
        filename = f"{output_dir}/{contact.replace(' ', '_')}_conflict.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Conflict analysis saved: {filename}")
        return filename

def main():
    """Run conflict analysis on top contacts"""
    ensure_user_consent()
    analyzer = ConflictAnalyzer()
    
    # Top 10 contacts by message volume
    contact_counts = analyzer.df["contact_name"].value_counts()
    contacts = list(contact_counts.head(10).index)
    
    print("🔄 Starting Conflict Analysis...")
    print("=" * 70)
    
    for contact in contacts:
        print(f"\n📊 Analyzing: {contact}")
        try:
            results = analyzer.analyze_contact(contact)
            
            if "error" not in results:
                analyzer.save_results(results)
                print(f"  ✓ Profile: {results['conflict_profile']}")
                if 'statistics' in results and 'total_conflicts' in results['statistics']:
                    print(f"  ✓ Conflicts: {results['statistics']['total_conflicts']}")
            else:
                print(f"  ⚠ {results['error']}")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Conflict analysis complete!")

if __name__ == "__main__":
    main()
