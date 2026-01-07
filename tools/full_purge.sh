#!/bin/bash
# ============================================================================
# AegisTwin Full Purge Script
# ============================================================================
# This script removes ALL personal data, old identities, and legacy code
# from the repository to prepare it for sale.
#
# IMPORTANT: This is DESTRUCTIVE. Make backups if needed.
# ============================================================================

set -e

echo "=============================================="
echo "AegisTwin Full Purge"
echo "=============================================="
echo ""
echo "This will PERMANENTLY DELETE:"
echo "  - graveyard/ (all quarantined PII data)"
echo "  - legacy/ (legacy code directories)"
echo "  - docs/PII_SCAN_REPORT.md (contains old paths)"
echo ""
echo "The following will be KEPT:"
echo "  - aegistwin/ (main package)"
echo "  - docs/ (cleaned documentation)"
echo "  - fixtures/ (synthetic data)"
echo "  - tools/ (utilities)"
echo "  - tests/ (test suite)"
echo "  - examples/ (usage examples)"
echo ""

read -p "Type 'DELETE ALL' to confirm: " confirm
if [ "$confirm" != "DELETE ALL" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting purge..."

# Remove graveyard (all PII)
if [ -d "graveyard" ]; then
    echo "Removing graveyard/..."
    rm -rf graveyard/
fi

# Remove legacy directories
if [ -d "legacy" ]; then
    echo "Removing legacy/..."
    rm -rf legacy/
fi

# Remove PII scan report (contains old paths with personal data)
if [ -f "docs/PII_SCAN_REPORT.md" ]; then
    echo "Removing docs/PII_SCAN_REPORT.md..."
    rm -f docs/PII_SCAN_REPORT.md
fi

echo ""
echo "=============================================="
echo "✅ Purge complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Regenerate PII scan report: python tools/pii_scan.py"
echo "2. Run tests: make test"
echo "3. Run demos: make demo"
echo "4. Commit changes: git add -A && git commit -m 'chore: Complete PII and identity purge'"
echo ""
