# AegisTwin Default Policy
# Rego policy for Open Policy Agent integration
#
# @ai_prompt: Modify this policy to customize authorization rules.
# @context_boundary: aegistwin/governance/policies/default.rego
#
# AI-GENERATED 2026-01-07

package aegistwin.authz

import future.keywords.if
import future.keywords.in
import future.keywords.contains

# Default deny
default allow := false

# Allow queries by default
allow if {
    input.action == "query"
}

# Allow ingestion from non-system sources
allow if {
    input.action == "ingest"
    not startswith(input.resource, "system.")
}

# Allow analysis operations
allow if {
    input.action == "analyze"
}

# Allow LLM queries to mock provider
allow if {
    input.action == "llm.query"
    input.resource == "llm.mock"
}

# Allow replay operations
allow if {
    input.action == "replay"
}

# Deny rules with reasons
deny contains reason if {
    input.resource == "system.shell"
    reason := "Shell access is forbidden"
}

deny contains reason if {
    input.resource == "system.exec"
    reason := "Direct execution is forbidden"
}

deny contains reason if {
    input.action == "export"
    contains(input.resource, "pii")
    reason := "PII export is not permitted"
}

deny contains reason if {
    input.resource == "network.external"
    reason := "External network access is restricted"
}

# Admin override - allow everything for admin actors
allow if {
    input.actor == "admin"
}

# Rate limiting could be implemented here
# rate_limit_exceeded if {
#     input.context.requests_per_minute > 100
# }
