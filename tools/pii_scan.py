#!/usr/bin/env python3
"""
PII Scanner for AegisTwin Repository

Scans the repository for potentially sensitive personal information that must be
quarantined before shipping. Outputs a detailed report and exits non-zero if any
suspicious content is found outside the /graveyard/ directory.

@ai_prompt: Use this scanner before any commit to ensure no PII leaks into production.
@context_boundary: tools/security
"""

import os
import re
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict

# VOCAB: PII = Personally Identifiable Information


@dataclass
class PIIFinding:
    """Represents a single PII detection finding."""
    file_path: str
    finding_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    line_number: Optional[int] = None
    match_preview: Optional[str] = None


@dataclass
class ScanResult:
    """Complete scan result with all findings."""
    scan_time: str
    total_files_scanned: int
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[Dict] = field(default_factory=list)
    quarantined_paths: List[str] = field(default_factory=list)


# Suspicious filename patterns (case-insensitive)
SUSPICIOUS_FILENAME_PATTERNS = [
    r'raw_data',
    r'contact',
    r'messages?(?:_complete)?',
    r'conversation',
    r'chat_session',
    r'chat\s*session',
    r'export',
    r'imessage',
    r'jessica',
    r'personal',
    r'private',
    r'secret',
    r'password',
    r'credential',
    r'backup',
    r'dump',
    r'phone\s*book',
    r'address\s*book',
    r'relationships?',
    r'_analysis\.json$',
    r'_deep_analysis\.json$',
]

# Suspicious directory patterns
SUSPICIOUS_DIR_PATTERNS = [
    r'summarized_conversations',
    r'raw_data',
    r'exports?',
    r'personal',
    r'private',
    r'backup',
    r'dumps?',
]

# File extensions to scan for content
SCANNABLE_EXTENSIONS = {'.csv', '.json', '.sqlite', '.txt', '.log', '.md', '.py'}

# Binary/data extensions that are suspicious by nature
SUSPICIOUS_DATA_EXTENSIONS = {'.sqlite', '.db', '.sqlite3', '.mdb'}

# Image extensions (suspicious if in data directories)
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.heic'}

# Content regex patterns for PII detection
PII_CONTENT_PATTERNS = [
    # Email addresses
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'email', 'MEDIUM'),
    # Phone numbers (various formats)
    (r'\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', 'phone_number', 'HIGH'),
    # Social Security Numbers
    (r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b', 'ssn_pattern', 'CRITICAL'),
    # Credit card patterns
    (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b', 'credit_card', 'CRITICAL'),
    # iMessage/Apple ID patterns
    (r'(?:imessage|apple\s*id|icloud)', 'apple_service', 'MEDIUM'),
    # Common name patterns with context (name: value or "name": "value")
    (r'["\']?(?:first_?name|last_?name|full_?name|user_?name|display_?name)["\']?\s*[:=]\s*["\']?[A-Z][a-z]+', 'name_field', 'HIGH'),
]

# Known personal names to flag (from the repo analysis)
KNOWN_PERSONAL_NAMES = [
    'jessica', 'becca', 'gabby', 'lily', 'marisa', 'max', 'mom', 'potato',
    'steph', 'ian', 'julia', 'oliver', 'phillip', 'sean', 'natalia', 'quinn',
]

# Paths that are allowed to contain PII (quarantine area)
ALLOWED_PII_PATHS = [
    'graveyard/',
    'graveyard/PII/',
    '.git/',
]


def is_path_allowed(path: str, repo_root: str) -> bool:
    """Check if path is in an allowed PII location."""
    rel_path = os.path.relpath(path, repo_root)
    for allowed in ALLOWED_PII_PATHS:
        if rel_path.startswith(allowed):
            return True
    return False


def check_filename_suspicious(filename: str) -> Tuple[bool, str]:
    """Check if filename matches suspicious patterns."""
    filename_lower = filename.lower()
    for pattern in SUSPICIOUS_FILENAME_PATTERNS:
        if re.search(pattern, filename_lower, re.IGNORECASE):
            return True, pattern
    return False, ""


def check_dir_suspicious(dir_path: str) -> Tuple[bool, str]:
    """Check if directory path matches suspicious patterns."""
    dir_lower = dir_path.lower()
    for pattern in SUSPICIOUS_DIR_PATTERNS:
        if re.search(pattern, dir_lower, re.IGNORECASE):
            return True, pattern
    return False, ""


def check_known_names(content: str) -> List[str]:
    """Check for known personal names in content."""
    found_names = []
    content_lower = content.lower()
    for name in KNOWN_PERSONAL_NAMES:
        # Look for name with word boundaries
        if re.search(rf'\b{name}\b', content_lower):
            found_names.append(name)
    return found_names


def scan_file_content(file_path: str, max_size_mb: int = 10) -> List[PIIFinding]:
    """Scan file content for PII patterns."""
    findings = []
    
    # Skip files that are too large
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        findings.append(PIIFinding(
            file_path=file_path,
            finding_type='large_data_file',
            severity='MEDIUM',
            description=f'Large data file ({file_size / 1024 / 1024:.1f}MB) - manual review needed'
        ))
        return findings
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return findings
    
    # Check for PII patterns
    for pattern, pii_type, severity in PII_CONTENT_PATTERNS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches:
            # Limit to first 5 matches per pattern
            for match in matches[:5]:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                # Get preview (redacted)
                preview = match.group(0)
                if len(preview) > 20:
                    preview = preview[:10] + '...' + preview[-5:]
                
                findings.append(PIIFinding(
                    file_path=file_path,
                    finding_type=pii_type,
                    severity=severity,
                    description=f'Found {pii_type} pattern',
                    line_number=line_num,
                    match_preview=f'[REDACTED: {preview[:3]}***]'
                ))
    
    # Check for known personal names
    found_names = check_known_names(content)
    if found_names:
        findings.append(PIIFinding(
            file_path=file_path,
            finding_type='personal_name',
            severity='HIGH',
            description=f'Contains personal names: {", ".join(found_names)}'
        ))
    
    return findings


def scan_sqlite_db(db_path: str) -> List[PIIFinding]:
    """Scan SQLite database for suspicious tables/columns."""
    findings = []
    suspicious_patterns = ['contact', 'message', 'user', 'person', 'phone', 'email', 'name']
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            table_lower = table_name.lower()
            for pattern in suspicious_patterns:
                if pattern in table_lower:
                    findings.append(PIIFinding(
                        file_path=db_path,
                        finding_type='suspicious_db_table',
                        severity='HIGH',
                        description=f'Database contains suspicious table: {table_name}'
                    ))
                    break
            
            # Check column names
            try:
                cursor.execute(f'PRAGMA table_info("{table_name}")')
                columns = cursor.fetchall()
                for col in columns:
                    col_name = col[1].lower() if col[1] else ''
                    for pattern in suspicious_patterns:
                        if pattern in col_name:
                            findings.append(PIIFinding(
                                file_path=db_path,
                                finding_type='suspicious_db_column',
                                severity='MEDIUM',
                                description=f'Table {table_name} has suspicious column: {col[1]}'
                            ))
                            break
            except:
                pass
        
        conn.close()
    except Exception as e:
        findings.append(PIIFinding(
            file_path=db_path,
            finding_type='db_scan_error',
            severity='LOW',
            description=f'Could not scan database: {str(e)}'
        ))
    
    return findings


def scan_repository(repo_root: str) -> ScanResult:
    """Scan entire repository for PII."""
    findings: List[PIIFinding] = []
    files_scanned = 0
    quarantined = []
    
    print(f"Scanning repository: {repo_root}")
    print("-" * 60)
    
    for root, dirs, files in os.walk(repo_root):
        # Skip git directory
        if '.git' in root:
            continue
        
        # Check if current directory is in allowed PII path
        if is_path_allowed(root, repo_root):
            rel_path = os.path.relpath(root, repo_root)
            if rel_path not in quarantined:
                quarantined.append(rel_path)
            continue
        
        # Check directory name
        dir_suspicious, dir_pattern = check_dir_suspicious(root)
        if dir_suspicious:
            rel_path = os.path.relpath(root, repo_root)
            findings.append(PIIFinding(
                file_path=rel_path,
                finding_type='suspicious_directory',
                severity='HIGH',
                description=f'Directory matches suspicious pattern: {dir_pattern}'
            ))
        
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, repo_root)
            
            # Skip if in allowed path
            if is_path_allowed(file_path, repo_root):
                continue
            
            files_scanned += 1
            ext = Path(filename).suffix.lower()
            
            # Check filename
            name_suspicious, name_pattern = check_filename_suspicious(filename)
            if name_suspicious:
                findings.append(PIIFinding(
                    file_path=rel_path,
                    finding_type='suspicious_filename',
                    severity='HIGH',
                    description=f'Filename matches suspicious pattern: {name_pattern}'
                ))
            
            # Check for suspicious data extensions
            if ext in SUSPICIOUS_DATA_EXTENSIONS:
                findings.append(PIIFinding(
                    file_path=rel_path,
                    finding_type='data_file',
                    severity='MEDIUM',
                    description=f'Data file that may contain PII: {ext}'
                ))
                # Scan SQLite databases
                if ext in {'.sqlite', '.sqlite3', '.db'}:
                    findings.extend(scan_sqlite_db(file_path))
            
            # Check for images in data directories
            if ext in IMAGE_EXTENSIONS:
                if any(d in root.lower() for d in ['data', 'export', 'output', 'report']):
                    findings.append(PIIFinding(
                        file_path=rel_path,
                        finding_type='suspicious_image',
                        severity='MEDIUM',
                        description='Image file in data directory - may contain personal info'
                    ))
            
            # Scan content of text files
            if ext in SCANNABLE_EXTENSIONS:
                content_findings = scan_file_content(file_path)
                findings.extend(content_findings)
    
    # Build result
    critical_count = sum(1 for f in findings if f.severity == 'CRITICAL')
    high_count = sum(1 for f in findings if f.severity == 'HIGH')
    medium_count = sum(1 for f in findings if f.severity == 'MEDIUM')
    low_count = sum(1 for f in findings if f.severity == 'LOW')
    
    return ScanResult(
        scan_time=datetime.now().isoformat(),
        total_files_scanned=files_scanned,
        total_findings=len(findings),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        findings=[asdict(f) for f in findings],
        quarantined_paths=quarantined
    )


def generate_report(result: ScanResult, output_path: str) -> None:
    """Generate markdown report from scan results."""
    with open(output_path, 'w') as f:
        f.write("# PII Scan Report\n\n")
        f.write(f"**Scan Time:** {result.scan_time}\n")
        f.write(f"**Files Scanned:** {result.total_files_scanned}\n")
        f.write(f"**Total Findings:** {result.total_findings}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"| Severity | Count |\n")
        f.write(f"|----------|-------|\n")
        f.write(f"| 🔴 CRITICAL | {result.critical_count} |\n")
        f.write(f"| 🟠 HIGH | {result.high_count} |\n")
        f.write(f"| 🟡 MEDIUM | {result.medium_count} |\n")
        f.write(f"| 🟢 LOW | {result.low_count} |\n\n")
        
        if result.quarantined_paths:
            f.write("## Quarantined Paths (Excluded from scan)\n\n")
            for path in result.quarantined_paths:
                f.write(f"- `{path}`\n")
            f.write("\n")
        
        if result.findings:
            f.write("## Findings\n\n")
            
            # Group by severity
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                severity_findings = [f for f in result.findings if f['severity'] == severity]
                if severity_findings:
                    f.write(f"### {severity} ({len(severity_findings)})\n\n")
                    for finding in severity_findings:
                        f.write(f"- **{finding['file_path']}**\n")
                        f.write(f"  - Type: `{finding['finding_type']}`\n")
                        f.write(f"  - {finding['description']}\n")
                        if finding.get('line_number'):
                            f.write(f"  - Line: {finding['line_number']}\n")
                        f.write("\n")
        
        f.write("\n---\n")
        f.write("## Recommended Actions\n\n")
        f.write("1. Move all flagged files to `/graveyard/PII/`\n")
        f.write("2. Add paths to `.gitignore`\n")
        f.write("3. Generate synthetic replacements where needed\n")
        f.write("4. Re-run this scanner to verify cleanup\n")
        f.write("5. Use `git filter-repo` to purge history if needed\n")


def main():
    """Main entry point."""
    # Determine repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    print("=" * 60)
    print("AegisTwin PII Scanner")
    print("=" * 60)
    
    # Run scan
    result = scan_repository(str(repo_root))
    
    # Generate report
    report_path = repo_root / "docs" / "PII_SCAN_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_report(result, str(report_path))
    
    # Print summary
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Files scanned: {result.total_files_scanned}")
    print(f"Total findings: {result.total_findings}")
    print(f"  🔴 CRITICAL: {result.critical_count}")
    print(f"  🟠 HIGH: {result.high_count}")
    print(f"  🟡 MEDIUM: {result.medium_count}")
    print(f"  🟢 LOW: {result.low_count}")
    print(f"\nReport saved to: {report_path}")
    
    # Exit with error if findings exist outside graveyard
    if result.total_findings > 0:
        print("\n⚠️  WARNING: PII detected outside quarantine area!")
        print("   Run Phase B to quarantine before proceeding.")
        sys.exit(1)
    else:
        print("\n✅ No PII detected. Safe to proceed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
