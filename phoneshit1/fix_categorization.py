import json
import os

def fix_categorization():
    """Fix categorization based on actual relationship data"""
    
    print("Loading data...")
    
    # Load contact database
    with open('DATA/analysis/contact_database.json', 'r') as f:
        contacts = json.load(f)
    
    # Load analyses
    analyses = {}
    for filename in os.listdir('DATA/analysis/'):
        if filename.endswith('_deep_analysis.json'):
            with open(f'DATA/analysis/{filename}', 'r') as f:
                data = json.load(f)
                analyses[data['person']] = data
    
    # Start with original categories as base
    with open('DATA/analysis/relationship_categories_BACKUP.json', 'r') as f:
        categories = json.load(f)
    
    print("\nApplying fixes based on analysis data...")
    
    # Fix 1: Move obvious family names from close_friends to family
    family_keywords = ["mom", "dad", "aunt", "uncle", "grandma", "grandpa", "sister", "brother"]
    moved_to_family = []
    for name in list(categories.get("close_friends", [])):
        lowered = name.lower()
        if any(k in lowered for k in family_keywords):
            categories["close_friends"].remove(name)
            if name not in categories["family"]:
                categories["family"].append(name)
            moved_to_family.append(name)
    if moved_to_family:
        print(f"✓ Moved to family: {', '.join(moved_to_family)}")
    
    # Fix 2: Identify romantic partners based on analysis
    romantic_partners = []
    ex_romantic_partners = []
    
    # Known romantic partners from analysis (optional, may be customized per dataset)
    known_romantic = []
    
    for name in known_romantic:
        analysis = analyses.get(name)
        if analysis:
            days_since = analysis.get('days_since_last', 999)
            status = analysis.get('status', '')
            love_count = analysis['emotional_keywords'].get('love', 0)
            
            # Current romantic partner: active status, recent contact, high love keywords
            if days_since < 30 and 'ENDED' not in status and love_count > 100:
                romantic_partners.append(name)
                print(f"✓ Identified {name} as current romantic partner")
            else:
                ex_romantic_partners.append(name)
                print(f"✓ Identified {name} as ex-romantic partner")
        else:
            # No analysis, check message count
            contact_data = contacts.get(name, {})
            msg_count = contact_data.get('message_count', 0)
            if msg_count > 30000:
                ex_romantic_partners.append(name)
                print(f"✓ Identified {name} as ex-romantic partner (high message count)")
    
    # Remove romantic partners from close_friends
    for name in known_romantic:
        if name in categories['close_friends']:
            categories['close_friends'].remove(name)
    
    # Update categories
    categories['romantic_partner'] = romantic_partners
    
    # Create ex_romantic_partner category if it doesn't exist
    if 'ex_romantic_partner' not in categories:
        categories['ex_romantic_partner'] = []
    categories['ex_romantic_partner'] = ex_romantic_partners
    
    # Fix 3: Identify more close friends based on criteria
    # Close friend criteria: 10k+ messages, active status, low breakup count
    potential_close_friends = []
    
    for name, analysis in analyses.items():
        if name in romantic_partners or name in ex_romantic_partners:
            continue
        if name in categories['family']:
            continue
        if '&' in name or '+' in name:  # Skip group chats
            continue
            
        msg_count = analysis.get('total_messages', 0)
        days_since = analysis.get('days_since_last', 999)
        status = analysis.get('status', '')
        breakup_count = analysis['emotional_keywords'].get('breakup', 0)
        
        # Close friend: 10k+ messages, active or recent contact, low breakup
        if msg_count >= 10000 and days_since < 90 and breakup_count < 20:
            if name not in categories['close_friends']:
                potential_close_friends.append(name)
    
    # Add potential close friends
    for name in potential_close_friends:
        if name not in categories['close_friends']:
            categories['close_friends'].append(name)
            print(f"✓ Added {name} to close_friends")
    
    # Print summary
    print("\n" + "="*60)
    print("FIXED CATEGORIZATION SUMMARY")
    print("="*60)
    
    print(f"\nromantic_partner: {len(categories['romantic_partner'])} contacts")
    for contact in categories['romantic_partner']:
        print(f"  - {contact}")
    
    print(f"\nex_romantic_partner: {len(categories['ex_romantic_partner'])} contacts")
    for contact in categories['ex_romantic_partner']:
        print(f"  - {contact}")
    
    print(f"\nclose_friends: {len(categories['close_friends'])} contacts")
    for contact in categories['close_friends']:
        print(f"  - {contact}")
    
    print(f"\nfamily: {len(categories['family'])} contacts")
    for contact in categories['family'][:10]:
        print(f"  - {contact}")
    if len(categories['family']) > 10:
        print(f"  ... and {len(categories['family']) - 10} more")
    
    print(f"\nacquaintances: {len(categories['acquaintances'])} contacts")
    print(f"group_chats: {len(categories['group_chats'])} contacts")
    
    # Save
    with open('DATA/analysis/relationship_categories.json', 'w') as f:
        json.dump(categories, f, indent=2)
    
    print("\n✓ Saved fixed categorization")
    
    return categories

if __name__ == '__main__':
    fix_categorization()
