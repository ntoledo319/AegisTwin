"""
Topic Mining Module - Conversation Theme Extraction

This module uses NLP techniques to:
- Extract conversation topics using LDA
- Track topic evolution over time
- Identify conflict-triggering subjects
- Cluster similar conversations
- Extract named entities
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# Import from existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis_pipeline import load_messages, build_contact_database
from ethics import load_ethics_config, assess_contact_from_deep_analysis, ensure_user_consent


class TopicMiner:
    """Extracts and analyzes conversation topics."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.stop_words = self._build_stop_words()
        
    def _build_stop_words(self) -> List[str]:
        """Build comprehensive stop word list."""
        basic_stops = [
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'what', 'when', 'where', 'who', 'which', 'why', 'how',
            'this', 'that', 'these', 'those',
            'not', 'no', 'yes', 'can', 'cant', 'dont', 'wont', 'im', 'id', 'ill', 'ive',
            'yeah', 'yea', 'ok', 'okay', 'haha', 'lol', 'lmao', 'omg', 'like', 'just', 'really',
            'so', 'very', 'too', 'much', 'more', 'most', 'some', 'any', 'all', 'both'
        ]
        return basic_stops
    
    def extract_topics(self, contact_name: str, n_topics: int = 10) -> Dict:
        """Extract main conversation topics using LDA."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 100:
            return {'error': 'Insufficient data for topic extraction'}
        
        # Prepare text data
        messages = contact_df['message'].dropna().astype(str)
        
        # Clean and preprocess
        messages_clean = messages.apply(self._clean_text)
        messages_clean = messages_clean[messages_clean.str.len() > 10]
        
        if len(messages_clean) < 50:
            return {'error': 'Insufficient meaningful text after cleaning'}
        
        # Create document-term matrix
        vectorizer = CountVectorizer(
            max_features=1000,
            stop_words=self.stop_words,
            min_df=5,
            max_df=0.7,
            ngram_range=(1, 2)
        )
        
        try:
            doc_term_matrix = vectorizer.fit_transform(messages_clean)
        except Exception as e:
            return {'error': f'Vectorization failed: {str(e)}'}
        
        # Fit LDA model
        lda = LatentDirichletAllocation(
            n_components=min(n_topics, 10),
            random_state=42,
            max_iter=50
        )
        
        try:
            lda.fit(doc_term_matrix)
        except Exception as e:
            return {'error': f'LDA fitting failed: {str(e)}'}
        
        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            
            # Infer topic label
            label = self._infer_topic_label(top_words)
            
            topics.append({
                'topic_id': topic_idx + 1,
                'label': label,
                'keywords': top_words[:7],
                'relevance_score': round(topic.sum(), 2)
            })
        
        # Calculate topic distribution across conversation
        doc_topics = lda.transform(doc_term_matrix)
        topic_prevalence = doc_topics.mean(axis=0)
        
        for i, topic in enumerate(topics):
            topic['prevalence'] = round(float(topic_prevalence[i]), 3)
        
        # Sort by prevalence
        topics.sort(key=lambda x: x['prevalence'], reverse=True)
        
        return {
            'contact': contact_name,
            'topics_extracted': len(topics),
            'topics': topics,
            'analysis_summary': self._summarize_topics(topics),
            'generated_at': datetime.now().isoformat()
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\d{3}[-.]?\d{3}[-.]?\d{4}', '', text)
        
        # Remove special characters but keep letters and spaces
        text = re.sub(r'[^a-z\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _infer_topic_label(self, keywords: List[str]) -> str:
        """Infer human-readable topic label from keywords."""
        # Define topic patterns
        patterns = {
            'Work & Career': ['work', 'job', 'boss', 'office', 'meeting', 'project', 'career', 'interview'],
            'Relationships & Dating': ['relationship', 'dating', 'love', 'boyfriend', 'girlfriend', 'together'],
            'Family': ['mom', 'dad', 'family', 'parent', 'brother', 'sister', 'grandma', 'grandpa'],
            'Social Plans': ['tonight', 'tomorrow', 'weekend', 'hang', 'meet', 'party', 'event', 'plans'],
            'Food & Dining': ['food', 'eat', 'dinner', 'lunch', 'restaurant', 'cook', 'meal'],
            'Entertainment': ['movie', 'show', 'watch', 'game', 'play', 'music', 'concert', 'netflix'],
            'Travel': ['trip', 'travel', 'vacation', 'visit', 'flight', 'drive'],
            'Health & Wellness': ['sick', 'doctor', 'hospital', 'health', 'therapy', 'exercise', 'gym'],
            'Emotions & Feelings': ['feel', 'feeling', 'happy', 'sad', 'excited', 'worried', 'stressed'],
            'School & Education': ['school', 'class', 'teacher', 'study', 'homework', 'exam', 'grade'],
            'Money & Finance': ['money', 'pay', 'cost', 'expensive', 'buy', 'afford'],
            'Friends & Social': ['friend', 'friends', 'people', 'everyone', 'hang out']
        }
        
        # Score each potential label
        scores = {}
        keywords_set = set(keywords)
        
        for label, pattern_words in patterns.items():
            overlap = len(keywords_set.intersection(set(pattern_words)))
            if overlap > 0:
                scores[label] = overlap
        
        if scores:
            return max(scores, key=scores.get)
        else:
            # Generic label based on first keyword
            return f"Topic: {keywords[0]}" if keywords else "General Conversation"
    
    def _summarize_topics(self, topics: List[Dict]) -> str:
        """Summarize main conversation themes."""
        if not topics:
            return "No clear topics identified"
        
        top_3 = topics[:3]
        labels = [t['label'] for t in top_3]
        
        return f"Primary themes: {', '.join(labels)}"
    
    def track_topic_evolution(self, contact_name: str) -> Dict:
        """Track how conversation topics change over time."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 200:
            return {'error': 'Insufficient data for evolution tracking'}
        
        contact_df = contact_df.sort_values('timestamp')
        
        # Split into phases
        phase_count = min(4, len(contact_df) // 100)
        phase_size = len(contact_df) // phase_count
        
        phase_topics = []
        
        for i in range(phase_count):
            start_idx = i * phase_size
            end_idx = (i + 1) * phase_size if i < phase_count - 1 else len(contact_df)
            phase_df = contact_df.iloc[start_idx:end_idx]
            
            # Extract top keywords for this phase
            messages = phase_df['message'].dropna().astype(str)
            messages_clean = messages.apply(self._clean_text)
            all_text = ' '.join(messages_clean)
            
            # Get word frequencies
            words = all_text.split()
            word_freq = Counter(w for w in words if w not in self.stop_words and len(w) > 3)
            
            top_keywords = [word for word, _ in word_freq.most_common(10)]
            
            phase_topics.append({
                'phase': i + 1,
                'period': f"{phase_df['timestamp'].min().strftime('%Y-%m')} to {phase_df['timestamp'].max().strftime('%Y-%m')}",
                'top_keywords': top_keywords,
                'theme': self._infer_topic_label(top_keywords)
            })
        
        # Analyze evolution
        evolution_summary = self._analyze_evolution(phase_topics)
        
        return {
            'contact': contact_name,
            'phases_analyzed': len(phase_topics),
            'phase_topics': phase_topics,
            'evolution_summary': evolution_summary,
            'generated_at': datetime.now().isoformat()
        }
    
    def _analyze_evolution(self, phase_topics: List[Dict]) -> str:
        """Analyze how topics evolved."""
        if len(phase_topics) < 2:
            return "Insufficient phases for evolution analysis"
        
        first_theme = phase_topics[0]['theme']
        last_theme = phase_topics[-1]['theme']
        
        if first_theme == last_theme:
            return f"Consistent focus on {first_theme} throughout relationship"
        else:
            return f"Evolved from {first_theme} to {last_theme}"
    
    def identify_conflict_topics(self, contact_name: str) -> Dict:
        """Identify topics that trigger conflict."""
        contact_df = self.df[self.df['chat_session'] == contact_name].copy()
        
        if len(contact_df) < 100:
            return {'error': 'Insufficient data for conflict topic analysis'}
        
        # Define conflict indicators
        conflict_words = ['fight', 'argue', 'angry', 'mad', 'upset', 'annoyed', 'frustrated']
        
        # Find messages with conflict language
        contact_df['has_conflict'] = contact_df['message'].astype(str).str.lower().apply(
            lambda x: any(word in x for word in conflict_words)
        )
        
        conflict_messages = contact_df[contact_df['has_conflict']].copy()
        
        if len(conflict_messages) < 10:
            return {
                'contact': contact_name,
                'conflict_detected': False,
                'message': 'Low conflict relationship - insufficient conflict messages for topic analysis'
            }
        
        # Extract keywords from conflict messages
        messages = conflict_messages['message'].dropna().astype(str)
        messages_clean = messages.apply(self._clean_text)
        all_text = ' '.join(messages_clean)
        
        words = all_text.split()
        word_freq = Counter(w for w in words if w not in self.stop_words and w not in conflict_words and len(w) > 3)
        
        conflict_topics = [word for word, count in word_freq.most_common(10)]
        
        return {
            'contact': contact_name,
            'conflict_detected': True,
            'conflict_message_count': len(conflict_messages),
            'conflict_message_percentage': round(len(conflict_messages) / len(contact_df) * 100, 2),
            'common_conflict_topics': conflict_topics,
            'primary_trigger': conflict_topics[0] if conflict_topics else 'Unknown',
            'assessment': self._assess_conflict_topics(conflict_topics),
            'generated_at': datetime.now().isoformat()
        }
    
    def _assess_conflict_topics(self, topics: List[str]) -> str:
        """Assess what conflict topics reveal."""
        if not topics:
            return "Unable to identify specific conflict triggers"
        
        # Common conflict categories
        if any(word in topics for word in ['money', 'pay', 'cost', 'afford']):
            return "Financial issues are a recurring conflict point"
        elif any(word in topics for word in ['time', 'busy', 'plans', 'cancel']):
            return "Scheduling and availability are sources of conflict"
        elif any(word in topics for word in ['friend', 'friends', 'people', 'hang']):
            return "Social circle and friendships cause tension"
        else:
            return f"Conflicts often center around: {topics[0]}"
    
    def generate_full_topic_report(self, contact_name: str) -> Dict:
        """Generate comprehensive topic analysis report."""
        topics = self.extract_topics(contact_name)
        evolution = self.track_topic_evolution(contact_name)
        conflicts = self.identify_conflict_topics(contact_name)
        
        return {
            'contact': contact_name,
            'topic_extraction': topics,
            'topic_evolution': evolution,
            'conflict_topics': conflicts,
            'generated_at': datetime.now().isoformat()
        }


def save_topic_report(report: Dict, output_dir: str = "outputs/topics"):
    """Save topic report to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    contact_safe = report['contact'].replace('/', '_')[:100]
    filename = f"{contact_safe}_topics_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filepath


def main():
    """Run topic mining on all contacts."""
    ensure_user_consent()
    print("=" * 60)
    print("TOPIC MINING ANALYSIS")
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
    
    # Initialize miner
    miner = TopicMiner(df)
    
    # Analyze top 10 contacts by message volume
    contact_counts = df["chat_session"].value_counts()
    priority_contacts = list(contact_counts.head(10).index)
    
    print("\nGenerating topic reports for top contacts...")
    
    for contact in priority_contacts:
        ethics_info = assess_contact_from_deep_analysis(contact, deep_analyses, ethics_config)
        print(f"\n{'='*60}")
        print(f"ANALYSIS: {contact}")
        print(f"{'='*60}")
        if ethics_info.get("detail_level") == "blocked":
            print("Ethical safeguards triggered; skipping detailed topic analysis.")
            continue
        
        report = miner.generate_full_topic_report(contact)
        filepath = save_topic_report(report)
        
        # Print summary
        if "topics_extracted" in report.get("topic_extraction", {}):
            print(
                f"\nTopics Extracted: "
                f"{report['topic_extraction']['topics_extracted']}"
            )
            print(f"Summary: {report['topic_extraction']['analysis_summary']}")
        
        if "conflict_detected" in report.get("conflict_topics", {}):
            if report["conflict_topics"]["conflict_detected"]:
                topics = report["conflict_topics"]["common_conflict_topics"][:3]
                print(f"Conflict Topics: {', '.join(topics)}")
        
        print(f"\nReport saved: {filepath}")
    
    print("\n" + "="*60)
    print("TOPIC MINING COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
