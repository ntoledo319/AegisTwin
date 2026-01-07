"""
High-level orchestrator to rebuild the core analysis, IQ/EI profile,
and relationship categorization/health scores in one go.

Usage:
    python rebuild_all_analysis.py
"""

from analysis_pipeline import main as rebuild_core
from intelligence_analysis import main as rebuild_intelligence
from relationship_categorization import main as rebuild_relationships


def main():
    print("=== STEP 1: Rebuilding core chat analysis (deep analyses, indices) ===")
    rebuild_core()
    print("\n=== STEP 2: Recomputing IQ/EI and communication profile ===")
    rebuild_intelligence()
    print("\n=== STEP 3: Rebuilding relationship categorization and health scores ===")
    rebuild_relationships()
    print("\nAll analysis artifacts rebuilt using the v2/v3 pipeline.")


if __name__ == "__main__":
    main()

