# HydraMind v1 — Code of Conduct ("Do No Evil")

**Short version:** Build useful things. Don't harm people. When in doubt, stop and ask.

## 0) Purpose & Scope

This Code applies to everyone using, contributing to, or deploying HydraMind: maintainers, contributors, customers, contractors, and operators—across code, docs, issues, deploys, and real-world use.

## 1) Golden Rules

* **First, do no harm.** If it could hurt people or communities, don't ship it.
* **Humans stay in charge.** Meaningful human oversight for any system that can affect safety, rights, health, or livelihood.
* **Consent & clarity.** No sneaky data grabs. Tell people what the system does, collects, and decides.
* **Least power necessary.** Give modules only the access they actually need.
* **Fail safe, not spectacular.** On anomaly or uncertainty, degrade gracefully or shut down.

## 2) Hard No's (Non-Negotiables)

HydraMind must not be used, trained, or configured for:

* **Violence or weaponization** (targeting, arming, autonomous harm, or equivalents).
* **Mass surveillance or repression** (tracking protected groups, unlawful monitoring).
* **Human rights abuses** (torture, forced labor, discriminatory profiling).
* **Illegal activity** (including evasion of law, malware C2, credential theft).
* **Exploitation** (stalking, harassment, doxxing, deepfake impersonation).
* **Medical/therapeutic claims** without licensed human professionals in the loop.
* **Child sexual abuse material (CSAM)** or any content endangering minors.
* **High-risk autonomy** (e.g., vehicles/drones/industrial robots) without certified safety layers, geofencing, and hard kill-switches.

If your use case even sniffs one of these: stop and open a review (see §7).

## 3) Sensitive & High-Risk Domains

For domains like healthcare, finance, public safety, mobility, and critical infrastructure:

* **Human-in-the-loop required.**
* **Transparent logging** of inputs, outputs, and interventions.
* **Pre-deployment risk assessment** and test plans.
* **Real-time anomaly detection** and hardware/soft kill-switches.
* **Rollback plan** and contact tree on-call.

## 4) Data & Privacy

* **Collect minimally.** Use the smallest, shortest-lived data you can.
* **Get consent** where applicable; honor opt-out.
* **Encrypt at rest & in transit;** segregate secrets; rotate keys.
* **No shadow datasets.** Document sources; respect licenses and TOS.
* **Redaction by default** in logs; only store what's needed for safety & audit.

## 5) Fairness & Inclusion

* **Strive to mitigate bias** in datasets and outputs; document known limits.
* **No discriminatory targeting** or exclusions based on protected traits.
* **Provide accessibility considerations** (a11y in UIs; alt paths for control).

## 6) Security Hygiene

* **Principle of least privilege** for modules, buses, and APIs.
* **Threat modeling** for new capabilities; fix critical vulns before release.
* **Signed builds,** reproducible deploys when possible.
* **No default credentials.** Rotate secrets. Rate-limit dangerous endpoints.

## 7) Review & Escalation ("Yellow & Red Zones")

* **Yellow-zone (needs review):** dual-use research, facial/body tracking, emotion inference, autonomous actuation, scraping at scale, political influence. File a Risk Review before shipping.
* **Red-zone (blocked):** any item in §2 Hard No's. Requires explicit maintainer exemption—which we do not grant.

**How to raise:** Open a private security/ethics ticket or email conduct@hydramind.dev with context, risks, mitigations, and rollback plan.

## 8) Transparency & Traceability

* **Keep CHANGELOG and ARCHITECTURE** current for safety-relevant changes.
* **Log decisions** that affect users (rate limits, bans, safety toggles).
* **Disclose synthetic content** or autonomy where it could matter to users.

## 9) Community Behavior

* **Be respectful.** No harassment, hate speech, or personal attacks.
* **Critique ideas, not people.** Assume good faith; provide evidence.
* **Honor contributor licenses,** attributions, and boundaries.

## 10) Enforcement

* **Light stuff:** warning → moderation of issues/PRs.
* **Serious stuff:** revoke access, reject contributions, ban accounts.
* **Grave violations:** notify platforms/hosts; report to authorities if required.

Maintainers decide in good faith, document outcomes, and can update this policy as needed.

## 11) Reporting

If you see abuse, risk, or violations:

* **Email conduct@hydramind.dev** or use the private "Report" channel.
* **Include:** what happened, links, screenshots/logs, potential harm, your contact.
* **We acknowledge receipt** within 72 hours and share next steps when possible.

## 12) License & Changes

This Code of Conduct is released under CC BY 4.0. Fork it; improve it; credit HydraMind.

**Version:** 1.0 • **Effective date:** 2024-01-01

---

**Bottom line:** HydraMind is power. Use it to help people—never to hurt them. If you're unsure: pause, escalate, and choose the path that leaves others safer than you found them.
