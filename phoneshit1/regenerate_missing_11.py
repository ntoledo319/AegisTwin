import json
import pandas as pd
import os
from generate_maximum_detail_reports import (
    load_messages_for_contact,
    generate_ultra_detailed_report
)

# Load data
with open('DATA/analysis/relationship_categories.json', 'r') as f:
    categories = json.load(f)

with open('DATA/analysis/contact_database.json', 'r') as f:
    contact_db = json.load(f)

# Contacts to regenerate
contacts_to_regenerate = [
    'Dr L', 'raccoon pounderer.', 'Rose', 'Isabel De Leon', 'Thot Daughter',
    'Cros', 'Mia Talamelli', 'Michael Kenny', 'Dad', 'Mom &amp; Dad', 'Mom'
]

print("Regenerating 11 missing reports...")

for i, contact in enumerate(contacts_to_regenerate, 1):
    print(f"\n[{i}/11] {contact}")
    
    # Load analysis
    safe_name = contact.replace('/', '_')[:100]
    analysis_path = f"DATA/analysis/{safe_name}_deep_analysis.json"
    
    if not os.path.exists(analysis_path):
        print(f"  ⚠️  No analysis found")
        continue
    
    with open(analysis_path, 'r') as f:
        analysis = json.load(f)
    
    # Load messages
    print(f"  Loading messages...")
    df_contact = load_messages_for_contact(contact)
    
    if len(df_contact) == 0:
        print(f"  ⚠️  No messages found")
        continue
    
    # Generate report
    print(f"  Generating report...")
    report = generate_ultra_detailed_report(contact, analysis, df_contact, categories, contact_db)
    
    # Determine output directory
    output_dir = 'REPORTS/04_INDIVIDUAL_PROFILES/individuals'
    for category, contacts_list in categories.items():
        if contact in contacts_list:
            if category == 'romantic_partner':
                output_dir = 'REPORTS/04_INDIVIDUAL_PROFILES/romantic'
            elif category == 'ex_romantic_partner':
                output_dir = 'REPORTS/04_INDIVIDUAL_PROFILES/romantic'
            elif category == 'close_friends':
                output_dir = 'REPORTS/04_INDIVIDUAL_PROFILES/friends'
            elif category == 'family':
                output_dir = 'REPORTS/04_INDIVIDUAL_PROFILES/family'
            break
    
    # Save
    output_path = f"{output_dir}/{contact}.md"
    with open(output_path, 'w') as f:
        f.write(report)
    
    word_count = len(report.split())
    print(f"  ✓ Saved ({word_count:,} words)")

print("\n✓ Completed regeneration of 11 reports")