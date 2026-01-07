#!/bin/bash
# ============================================================================
# AegisTwin Git History Purge Script
# ============================================================================
# This script uses git-filter-repo to permanently remove PII from git history.
# 
# IMPORTANT: This is a DESTRUCTIVE operation. Make sure you have backups.
# After running, all collaborators must re-clone the repository.
#
# @ai_prompt: Run this only after all PII is quarantined and verified.
# @context_boundary: tools/security
# ============================================================================

set -e

echo "=============================================="
echo "AegisTwin Git History Purge"
echo "=============================================="

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo ""
    echo "ERROR: git-filter-repo is not installed."
    echo ""
    echo "Install with one of:"
    echo "  pip install git-filter-repo"
    echo "  brew install git-filter-repo"
    echo ""
    echo "See: https://github.com/newren/git-filter-repo"
    exit 1
fi

# Verify we're in a git repo
if [ ! -d ".git" ]; then
    echo "ERROR: Not in a git repository root."
    exit 1
fi

# Warn the user
echo ""
echo "⚠️  WARNING: This will permanently rewrite git history!"
echo ""
echo "The following paths will be REMOVED from all commits:"
echo "  - phoneshit1/"
echo "  - DigitalTwin/summarized_conversations/"
echo "  - DigitalTwin/messages_complete.json.zip"
echo "  - DigitalTwin/data/"
echo "  - DigitalTwin/logs/"
echo "  - DigitalTwin/outputs/"
echo "  - HydraMind_v1/brain_events.sqlite"
echo "  - HydraMind_v1/logs/"
echo "  - HydraMind_v1/snapshots/"
echo "  - Any file matching: *jessica*, *contact*, *messages*.csv"
echo ""
echo "This operation CANNOT be undone."
echo ""

read -p "Type 'PURGE' to confirm: " confirm
if [ "$confirm" != "PURGE" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Creating backup tag before purge..."
git tag -f pre-purge-backup

echo ""
echo "Running git-filter-repo..."

# Paths to remove completely
git filter-repo --force \
    --path phoneshit1/ \
    --path DigitalTwin/summarized_conversations/ \
    --path DigitalTwin/messages_complete.json.zip \
    --path DigitalTwin/data/ \
    --path DigitalTwin/logs/ \
    --path DigitalTwin/outputs/ \
    --path HydraMind_v1/brain_events.sqlite \
    --path HydraMind_v1/logs/ \
    --path HydraMind_v1/snapshots/ \
    --invert-paths

# Remove files by pattern
echo ""
echo "Removing files matching PII patterns..."
git filter-repo --force \
    --path-glob '*jessica*' \
    --path-glob '*contact_database*' \
    --path-glob '*messages*.csv' \
    --path-glob '*conversation*.txt' \
    --path-glob '*raw_data*' \
    --invert-paths

echo ""
echo "=============================================="
echo "✅ Git history purge complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Verify the repo with: git log --all --oneline | head -20"
echo "2. Run PII scanner: python tools/pii_scan.py"
echo "3. If pushing to remote:"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "⚠️  All collaborators must re-clone the repository!"
echo ""
