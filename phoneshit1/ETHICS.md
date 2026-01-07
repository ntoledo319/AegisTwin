# Ethics & Safety Guidelines

This project analyzes message data to help people understand their own
communication and relationship patterns. It is **not** intended for:

- Stalking, harassment, or retaliation
- Coercive control or emotional manipulation
- Surveillance of partners, friends, employees, or strangers

The system is built with a few simple principles:

- **Self‑insight, not surveillance** – Focus analysis on your own behavior and
  how you show up in relationships.
- **Respect for autonomy** – Avoid using these tools to monitor or control
  others, especially without their knowledge or consent.
- **Do no harm** – When in doubt, prefer boundaries, de‑escalation, and
  support‑seeking over “winning” or “punishing” in relationships.

## Technical Safeguards

- All active analysis code runs on a generic CSV of messages and does not
  hard‑code any specific names or identities.
- Contact selection for analysis is *data‑driven* (e.g., top contacts by
  message volume) rather than targeting fixed individuals.
- The `ethics.py` module provides:
  - A configurable set of heuristics to assess ethical risk per contact
  - A consent handshake for CLI entrypoints so users explicitly agree to
    use the system responsibly
- The orchestrator and other CLI tools can use this ethics layer to:
  - Skip or limit detailed analysis for contacts with very one‑sided,
    highly conflictual, or very old/ended interactions
  - Embed ethical context into aggregated outputs

## Your Responsibility

No technical safeguard is perfect. As a user, you are responsible for:

- Only analyzing data you have a right to use
- Not using the outputs to intimidate, threaten, or manipulate others
- Seeking professional help where appropriate (this project is not a
  diagnostic or therapeutic tool)

If you are working on extensions to this codebase, keep these principles
in mind when adding new modules, metrics, or visualizations. Prefer
features that support:

- Self‑awareness
- Boundary‑setting
- Repair and reconciliation
- Letting go of unhealthy dynamics

