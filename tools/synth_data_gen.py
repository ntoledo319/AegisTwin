#!/usr/bin/env python3
"""
Synthetic Data Generator for AegisTwin

Generates synthetic personal data for demos and testing that mimics real-world
patterns without containing any actual PII.

@ai_prompt: Use this to generate demo data. All names/emails/content are fictional.
@context_boundary: tools/data_generation
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import hashlib

# VOCAB: Synthetic = Artificially generated, contains no real personal data

# Fictional first names (gender-neutral mix)
FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery",
    "Parker", "Sage", "Reese", "Finley", "Charlie", "Drew", "Skyler", "Jamie",
    "Robin", "Phoenix", "River", "Emery", "Dakota", "Cameron", "Hayden", "Blake"
]

# Fictional last names
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson",
    "Martin", "Lee", "Thompson", "White", "Harris", "Clark", "Lewis", "Robinson"
]

# Fictional company domains
DOMAINS = [
    "example.com", "acme-corp.test", "widget-co.example", "testmail.invalid",
    "demo-org.test", "sample-inc.example", "fictional.test", "notreal.example"
]

# Message topics (neutral, non-personal)
TOPICS = [
    "project update", "meeting schedule", "quarterly review", "team sync",
    "document review", "status report", "action items", "follow-up",
    "weekly summary", "planning session", "feedback request", "announcement"
]

# Message templates (neutral, professional)
MESSAGE_TEMPLATES = [
    "Hi {name}, just wanted to follow up on the {topic}. Let me know your thoughts.",
    "Quick update on {topic}: everything is on track for the deadline.",
    "Could you review the {topic} when you get a chance? Thanks!",
    "Reminder: {topic} is scheduled for tomorrow at {time}.",
    "Thanks for the update on {topic}. I'll review and get back to you.",
    "FYI - I've completed the {topic}. See attached for details.",
    "Let's discuss the {topic} in our next sync. Sound good?",
    "Great progress on {topic}! Keep up the good work.",
]

# Calendar event types
EVENT_TYPES = [
    "Team Meeting", "1:1 Sync", "Project Review", "Planning Session",
    "Training", "Workshop", "Presentation", "Interview", "Demo", "Standup"
]


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())[:8]


def generate_email(first: str, last: str) -> str:
    """Generate a synthetic email address."""
    domain = random.choice(DOMAINS)
    formats = [
        f"{first.lower()}.{last.lower()}@{domain}",
        f"{first.lower()}{last.lower()[0]}@{domain}",
        f"{first.lower()}_{last.lower()}@{domain}",
    ]
    return random.choice(formats)


def generate_phone() -> str:
    """Generate a synthetic phone number (555 prefix = fictional)."""
    return f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}"


def generate_contact() -> Dict[str, Any]:
    """Generate a synthetic contact."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "id": generate_id(),
        "first_name": first,
        "last_name": last,
        "email": generate_email(first, last),
        "phone": generate_phone(),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
    }


def generate_message(sender: Dict, recipient: Dict, timestamp: datetime) -> Dict[str, Any]:
    """Generate a synthetic message."""
    topic = random.choice(TOPICS)
    template = random.choice(MESSAGE_TEMPLATES)
    time_str = f"{random.randint(9,17)}:{random.choice(['00','15','30','45'])}"
    
    content = template.format(
        name=recipient["first_name"],
        topic=topic,
        time=time_str
    )
    
    return {
        "id": generate_id(),
        "sender_id": sender["id"],
        "sender_name": f"{sender['first_name']} {sender['last_name']}",
        "recipient_id": recipient["id"],
        "recipient_name": f"{recipient['first_name']} {recipient['last_name']}",
        "content": content,
        "timestamp": timestamp.isoformat(),
        "thread_id": hashlib.md5(f"{sender['id']}-{recipient['id']}".encode()).hexdigest()[:8],
        "is_read": random.choice([True, True, True, False]),
    }


def generate_calendar_event(owner: Dict, attendees: List[Dict], start: datetime) -> Dict[str, Any]:
    """Generate a synthetic calendar event."""
    event_type = random.choice(EVENT_TYPES)
    duration_minutes = random.choice([30, 45, 60, 90, 120])
    
    return {
        "id": generate_id(),
        "title": f"{event_type} - {random.choice(TOPICS).title()}",
        "owner_id": owner["id"],
        "owner_name": f"{owner['first_name']} {owner['last_name']}",
        "attendees": [
            {"id": a["id"], "name": f"{a['first_name']} {a['last_name']}", "email": a["email"]}
            for a in attendees
        ],
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(minutes=duration_minutes)).isoformat(),
        "location": random.choice(["Conference Room A", "Zoom", "Teams", "Room 101", "Virtual"]),
        "description": f"Discussion about {random.choice(TOPICS)}.",
    }


def generate_email_message(sender: Dict, recipients: List[Dict], timestamp: datetime) -> Dict[str, Any]:
    """Generate a synthetic email."""
    topic = random.choice(TOPICS)
    
    return {
        "id": generate_id(),
        "message_id": f"<{generate_id()}@{random.choice(DOMAINS)}>",
        "from": {"name": f"{sender['first_name']} {sender['last_name']}", "email": sender["email"]},
        "to": [{"name": f"{r['first_name']} {r['last_name']}", "email": r["email"]} for r in recipients],
        "subject": f"Re: {topic.title()}",
        "body": f"Hi team,\n\nJust a quick update on the {topic}.\n\nBest,\n{sender['first_name']}",
        "timestamp": timestamp.isoformat(),
        "has_attachments": random.choice([True, False, False, False]),
    }


def generate_dataset(
    num_contacts: int = 20,
    num_messages: int = 100,
    num_events: int = 30,
    num_emails: int = 50
) -> Dict[str, Any]:
    """Generate a complete synthetic dataset."""
    
    # Generate contacts
    contacts = [generate_contact() for _ in range(num_contacts)]
    
    # Generate messages
    messages = []
    base_time = datetime.now() - timedelta(days=30)
    for i in range(num_messages):
        sender = random.choice(contacts)
        recipient = random.choice([c for c in contacts if c["id"] != sender["id"]])
        timestamp = base_time + timedelta(hours=random.randint(0, 720))
        messages.append(generate_message(sender, recipient, timestamp))
    
    # Sort by timestamp
    messages.sort(key=lambda x: x["timestamp"])
    
    # Generate calendar events
    events = []
    for i in range(num_events):
        owner = random.choice(contacts)
        num_attendees = random.randint(1, 5)
        attendees = random.sample([c for c in contacts if c["id"] != owner["id"]], 
                                   min(num_attendees, len(contacts)-1))
        start = datetime.now() + timedelta(days=random.randint(-7, 14), hours=random.randint(9, 17))
        events.append(generate_calendar_event(owner, attendees, start))
    
    events.sort(key=lambda x: x["start_time"])
    
    # Generate emails
    emails = []
    for i in range(num_emails):
        sender = random.choice(contacts)
        num_recipients = random.randint(1, 3)
        recipients = random.sample([c for c in contacts if c["id"] != sender["id"]], 
                                    min(num_recipients, len(contacts)-1))
        timestamp = base_time + timedelta(hours=random.randint(0, 720))
        emails.append(generate_email_message(sender, recipients, timestamp))
    
    emails.sort(key=lambda x: x["timestamp"])
    
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "AegisTwin Synthetic Data Generator",
            "version": "1.0.0",
            "is_synthetic": True,
            "warning": "This is entirely fictional data for demonstration purposes only."
        },
        "contacts": contacts,
        "messages": messages,
        "calendar_events": events,
        "emails": emails,
    }


def main():
    """Generate synthetic fixtures."""
    print("=" * 60)
    print("AegisTwin Synthetic Data Generator")
    print("=" * 60)
    
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    fixtures_dir = repo_root / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate small dataset for quick demos
    print("\nGenerating small demo dataset...")
    small_data = generate_dataset(num_contacts=10, num_messages=25, num_events=10, num_emails=15)
    
    with open(fixtures_dir / "demo_small.json", "w") as f:
        json.dump(small_data, f, indent=2)
    print(f"  -> {fixtures_dir / 'demo_small.json'}")
    
    # Generate medium dataset
    print("\nGenerating medium dataset...")
    medium_data = generate_dataset(num_contacts=20, num_messages=100, num_events=30, num_emails=50)
    
    with open(fixtures_dir / "demo_medium.json", "w") as f:
        json.dump(medium_data, f, indent=2)
    print(f"  -> {fixtures_dir / 'demo_medium.json'}")
    
    # Generate individual fixture files
    print("\nGenerating individual fixtures...")
    
    with open(fixtures_dir / "contacts.json", "w") as f:
        json.dump({"contacts": small_data["contacts"], "metadata": small_data["metadata"]}, f, indent=2)
    
    with open(fixtures_dir / "messages.json", "w") as f:
        json.dump({"messages": small_data["messages"][:10], "metadata": small_data["metadata"]}, f, indent=2)
    
    with open(fixtures_dir / "calendar_events.json", "w") as f:
        json.dump({"events": small_data["calendar_events"][:5], "metadata": small_data["metadata"]}, f, indent=2)
    
    with open(fixtures_dir / "emails.json", "w") as f:
        json.dump({"emails": small_data["emails"][:5], "metadata": small_data["metadata"]}, f, indent=2)
    
    print(f"  -> contacts.json, messages.json, calendar_events.json, emails.json")
    
    print("\n" + "=" * 60)
    print("✅ Synthetic data generation complete!")
    print(f"   All fixtures saved to: {fixtures_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
