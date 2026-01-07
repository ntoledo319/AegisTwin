"""
Full Analysis Orchestration Script
Phase 7 - Master Orchestration

Runs all analytical modules in sequence and generates comprehensive outputs:
- Analytics: Predictive, Pattern, Topic, Sentiment
- Psychology: Attachment, Communication, Conflict
- Reporting: Enhanced reports, trends, comparisons
- Visualization: Dashboards and plots
- Monitoring: Health tracking and alerts
"""

import sys
import os
import json
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all analysis modules
from analytics.predictive_analysis import (
    RelationshipPredictor,
    save_prediction_report,
)
from analytics.pattern_detection import PatternDetector, save_pattern_report
from analytics.topic_mining import TopicMiner, save_topic_report
from analytics.sentiment_evolution import SentimentAnalyzer, save_sentiment_report
from psychology.attachment_analysis import AttachmentAnalyzer, save_attachment_report
from psychology.communication_evolution import CommunicationEvolutionAnalyzer
from psychology.conflict_analysis import ConflictAnalyzer
from analysis_pipeline import load_messages, build_contact_database, rebuild_all_deep_analyses
from ethics import load_ethics_config, assess_contact_from_deep_analysis

class FullAnalysisOrchestrator:
    """Orchestrates execution of all analysis modules"""
    
    def __init__(self, data_path='DATA/raw/messages.csv'):
        """Initialize orchestrator and core analysis objects."""
        self.data_path = data_path
        self.results = {}
        self.contacts = []
        self.ethics_config = load_ethics_config()
        
        print("🔧 Loading messages and building core analyses...")
        self.df = load_messages(data_path)
        self.contact_db, self.chat_stats = build_contact_database(self.df)
        self.deep_analyses = rebuild_all_deep_analyses(self.df, self.chat_stats)
        # Default priority contacts: top 10 non-system chats by message volume
        sorted_chats = sorted(
            (
                (name, stats.message_count)
                for name, stats in self.chat_stats.items()
                if stats.type != "system"
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        self.priority_contacts = [name for name, _ in sorted_chats[:10]]
        
        # Initialize all analyzers on top of shared data
        print("🔧 Initializing analysis modules...")
        self.predictive = RelationshipPredictor(self.df, self.deep_analyses)
        self.pattern = PatternDetector(self.df)
        self.topic = TopicMiner(self.df)
        self.sentiment = SentimentAnalyzer(self.df)
        self.attachment = AttachmentAnalyzer(self.df)
        self.communication = CommunicationEvolutionAnalyzer(data_path)
        self.conflict = ConflictAnalyzer(data_path)
        
        print("✅ All modules initialized\n")

    def _assess_contact_ethics(self, contact: str) -> dict:
        """Return ethics assessment for a contact using deep analysis data."""
        return assess_contact_from_deep_analysis(contact, self.deep_analyses, self.ethics_config)
    
    def _run_predictive(self, contact: str):
        """Run predictive analysis with safety checks."""
        if contact not in self.deep_analyses:
            return {"error": "Contact not found in deep analysis index"}
        return self.predictive.generate_full_prediction_report(contact)

    def _run_patterns(self, contact: str):
        """Run pattern detection for a contact."""
        if contact not in self.df["chat_session"].unique():
            return {"error": "Contact not found in dataset"}
        return self.pattern.generate_full_pattern_report(contact)

    def _run_topics(self, contact: str):
        """Run topic mining for a contact."""
        if contact not in self.df["chat_session"].unique():
            return {"error": "Contact not found in dataset"}
        return self.topic.generate_full_topic_report(contact)

    def _run_sentiment(self, contact: str):
        """Run sentiment evolution analysis for a contact."""
        if contact not in self.df["chat_session"].unique():
            return {"error": "Contact not found in dataset"}
        return self.sentiment.generate_full_sentiment_report(contact)

    def _run_attachment(self, contact: str):
        """Run attachment analysis for a contact."""
        return self.attachment.generate_full_attachment_report(contact)
    
    def run_all_analyses(self, contacts=None, skip_errors=True):
        """Run all analyses on specified contacts"""
        if contacts is None:
            contacts = self.priority_contacts
        
        self.contacts = contacts
        total_contacts = len(contacts)
        
        print("=" * 80)
        print(f"🚀 STARTING FULL ANALYSIS - {total_contacts} CONTACTS")
        print("=" * 80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for idx, contact in enumerate(contacts, 1):
            print(f"\n{'=' * 80}")
            print(f"📊 CONTACT {idx}/{total_contacts}: {contact}")
            print(f"{'=' * 80}\n")

            ethics_info = self._assess_contact_ethics(contact)
            
            contact_results = {
                "contact": contact,
                "analysis_timestamp": datetime.now().isoformat(),
                "ethics": ethics_info,
                "modules": {}
            }

            if ethics_info.get("detail_level") == "blocked":
                print("  ⚠️  Skipping detailed analysis for this contact due to ethical safeguards.")
                self.results[contact] = contact_results
                continue
            
            # Run each module
            modules = [
                ("Predictive Analysis", self._run_predictive, "predictive"),
                ("Pattern Detection", self._run_patterns, "patterns"),
                ("Topic Mining", self._run_topics, "topics"),
                ("Sentiment Evolution", self._run_sentiment, "sentiment"),
                ("Attachment Analysis", self._run_attachment, "attachment"),
                ("Communication Evolution", self.communication.analyze_contact, "communication"),
                ("Conflict Analysis", self.conflict.analyze_contact, "conflict")
            ]
            
            for module_name, analyzer_func, key in modules:
                try:
                    print(f"  🔄 Running {module_name}...", end=" ")
                    result = analyzer_func(contact)
                    
                    if "error" not in result:
                        contact_results["modules"][key] = result
                        print("✅")
                        
                        # Save individual module output
                        self._save_module_output(contact, key, result)
                    else:
                        print(f"⚠️  {result['error']}")
                        if not skip_errors:
                            contact_results["modules"][key] = result
                
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    if not skip_errors:
                        contact_results["modules"][key] = {"error": str(e)}
            
            # Store results
            self.results[contact] = contact_results
            
            # Generate summary for this contact
            self._print_contact_summary(contact, contact_results)
        
        print(f"\n{'=' * 80}")
        print("✅ ALL ANALYSES COMPLETE")
        print(f"{'=' * 80}\n")
        
        # Generate master summary
        self._generate_master_summary()
        
        return self.results
    
    def _save_module_output(self, contact, module_key, result):
        """Save individual module output via module-specific helpers."""
        try:
            if module_key == "predictive":
                save_prediction_report(result)
            elif module_key == "patterns":
                save_pattern_report(result)
            elif module_key == "topics":
                save_topic_report(result)
            elif module_key == "sentiment":
                save_sentiment_report(result)
            elif module_key == "attachment":
                save_attachment_report(result)
            elif module_key == "communication":
                self.communication.save_results(result)
            elif module_key == "conflict":
                self.conflict.save_results(result)
        except Exception as e:
            print(f"    ⚠️  Failed to save {module_key} output for {contact}: {e}")
    
    def _print_contact_summary(self, contact, contact_results):
        """Print summary for a contact"""
        print(f"\n  📋 SUMMARY FOR {contact}:")
        print(f"  {'-' * 76}")
        
        modules_run = len(contact_results["modules"])
        print(f"  ✓ Modules completed: {modules_run}/7")
        
        # Key insights
        insights = []
        
        if "predictive" in contact_results["modules"]:
            pred = contact_results["modules"]["predictive"]
            # New predictive reports nest risk info under breakup_risk_assessment
            risk_block = pred.get("breakup_risk_assessment", pred)
            if "risk_score" in risk_block:
                insights.append(f"Risk Score: {risk_block['risk_score']}/100")
        
        if "patterns" in contact_results["modules"]:
            patt = contact_results["modules"]["patterns"]
            # New pattern reports store anomalies under anomaly_detection
            anomalies_block = patt.get("anomaly_detection", patt)
            if "anomalies_detected" in anomalies_block:
                insights.append(f"Anomalies: {anomalies_block['anomalies_detected']}")
        
        if "conflict" in contact_results["modules"]:
            conf = contact_results["modules"]["conflict"]
            if "conflict_profile" in conf:
                insights.append(f"Conflict: {conf['conflict_profile']}")
        
        if "attachment" in contact_results["modules"]:
            att = contact_results["modules"]["attachment"]
            if "relationship_specific" in att and "your_style_with_them" in att["relationship_specific"]:
                insights.append(f"Attachment: {att['relationship_specific']['your_style_with_them']}")
        
        for insight in insights:
            print(f"  • {insight}")
        
        print()
    
    def _generate_master_summary(self):
        """Generate master summary of all analyses"""
        summary_file = "outputs/MASTER_ANALYSIS_SUMMARY.json"
        
        summary = {
            "analysis_date": datetime.now().isoformat(),
            "total_contacts_analyzed": len(self.contacts),
            "contacts": list(self.contacts),
            "results": self.results,
            "statistics": {
                "total_modules_run": sum(
                    len(r["modules"]) for r in self.results.values()
                ),
                "successful_analyses": sum(
                    1 for r in self.results.values() 
                    if len(r["modules"]) >= 5
                )
            }
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"📄 Master summary saved: {summary_file}")
        
        # Print final statistics
        print(f"\n📊 FINAL STATISTICS:")
        print(f"  • Contacts analyzed: {summary['statistics']['total_modules_run'] // 7}")
        print(f"  • Total module runs: {summary['statistics']['total_modules_run']}")
        print(f"  • Successful analyses: {summary['statistics']['successful_analyses']}")
        print(f"  • Output directory: outputs/")
    
    def run_single_module(self, module_name, contact):
        """Run a single module on a contact"""
        modules = {
            "predictive": (self._run_predictive, "Predictive Analysis"),
            "patterns": (self._run_patterns, "Pattern Detection"),
            "topics": (self._run_topics, "Topic Mining"),
            "sentiment": (self._run_sentiment, "Sentiment Evolution"),
            "attachment": (self._run_attachment, "Attachment Analysis"),
            "communication": (self.communication.analyze_contact, "Communication Evolution"),
            "conflict": (self.conflict.analyze_contact, "Conflict Analysis")
        }
        
        if module_name not in modules:
            print(f"❌ Unknown module: {module_name}")
            print(f"Available modules: {', '.join(modules.keys())}")
            return None
        
        analyzer_func, display_name = modules[module_name]
        
        print(f"🔄 Running {display_name} for {contact}...")
        
        try:
            result = analyzer_func(contact)
            
            if "error" not in result:
                self._save_module_output(contact, module_name, result)
                print(f"✅ {display_name} complete")
                return result
            else:
                print(f"⚠️  {result['error']}")
                return result
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {"error": str(e)}
    
    def export_to_csv(self, output_file="outputs/analysis_export.csv"):
        """Export key metrics to CSV for easy review"""
        if not self.results:
            print("⚠️  No results to export. Run analyses first.")
            return
        
        rows = []
        
        for contact, data in self.results.items():
            row = {"contact": contact}
            
            # Extract key metrics from each module
            if "predictive" in data["modules"]:
                pred = data["modules"]["predictive"]
                risk_block = pred.get("breakup_risk_assessment", pred)
                row["risk_score"] = risk_block.get("risk_score", "N/A")
                row["risk_level"] = risk_block.get("risk_level", "N/A")
            
            if "patterns" in data["modules"]:
                patt = data["modules"]["patterns"]
                anomalies_block = patt.get("anomaly_detection", patt)
                turning_block = patt.get("turning_points", {})
                row["anomalies"] = anomalies_block.get("anomalies_detected", "N/A")
                row["turning_points"] = turning_block.get("turning_points_detected", "N/A")
            
            if "sentiment" in data["modules"]:
                sent = data["modules"]["sentiment"]
                prog = sent.get("sentiment_progression", {})
                overall = prog.get("overall_sentiment", {})
                vol_block = sent.get("emotional_volatility", {})
                row["sentiment_score"] = overall.get("mean", "N/A")
                row["volatility"] = vol_block.get("volatility_score", "N/A")
            
            if "conflict" in data["modules"]:
                conf = data["modules"]["conflict"]
                row["conflict_profile"] = conf.get("conflict_profile", "N/A")
                if "statistics" in conf:
                    row["total_conflicts"] = conf["statistics"].get("total_conflicts", "N/A")
            
            if "attachment" in data["modules"]:
                att = data["modules"]["attachment"]
                if "relationship_specific" in att:
                    row["attachment_style"] = att["relationship_specific"].get("your_style_with_them", "N/A")
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"📊 Exported metrics to: {output_file}")

def main():
    """Main execution function"""
    import argparse
    from ethics import ensure_user_consent
    
    ensure_user_consent()

    parser = argparse.ArgumentParser(description="Run comprehensive relationship analysis")
    parser.add_argument("--contact", type=str, help="Analyze single contact")
    parser.add_argument("--module", type=str, help="Run specific module only")
    parser.add_argument("--all", action="store_true", help="Run all analyses on all priority contacts")
    parser.add_argument("--export-csv", action="store_true", help="Export results to CSV")
    
    args = parser.parse_args()
    
    orchestrator = FullAnalysisOrchestrator()
    
    if args.contact and args.module:
        # Single module, single contact
        orchestrator.run_single_module(args.module, args.contact)
    
    elif args.contact:
        # All modules, single contact
        orchestrator.run_all_analyses(contacts=[args.contact])
    
    elif args.all or (not args.contact and not args.module):
        # All modules, all priority contacts (default)
        orchestrator.run_all_analyses()
        
        if args.export_csv:
            orchestrator.export_to_csv()
    
    else:
        print("❌ Invalid arguments. Use --help for usage information.")

if __name__ == "__main__":
    main()
