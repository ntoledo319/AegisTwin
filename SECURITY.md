# Security Policy

## Reporting Security Vulnerabilities

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@aegistwin.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

## Security Update Process

1. **Report received** — Security team acknowledges within 48 hours
2. **Triage** — Assess severity and impact (1-3 business days)
3. **Fix development** — Develop and test fix in private repository
4. **Disclosure** — Coordinated disclosure with reporter
5. **Release** — Patched version released with security advisory

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

### Built-in Protections

AegisTwin includes several security features:

- **Policy Enforcement** — Configurable gates prevent unauthorized actions
- **Audit Logging** — All actions logged with actor, resource, outcome
- **Input Validation** — Pydantic schemas validate all event data
- **No SQL Injection** — No raw SQL queries (uses ORM when applicable)
- **No Code Execution** — No `eval()` or `exec()` of untrusted input

### Data Privacy

- **Local-First** — No data sent to external services by default
- **PII Scanner** — Automated detection of personal information
- **Synthetic Fixtures** — All demo data is fictional
- **Quarantine System** — Real data isolated in `/graveyard/PII/`

### Dependency Security

We regularly audit dependencies for known vulnerabilities:

```bash
# Check for known vulnerabilities
pip install safety
safety check --json

# Verify dependency licenses
pip install pip-licenses
pip-licenses --format=markdown
```

## Known Limitations

### Not Production-Hardened (v0.1.x)

This is an alpha release. The following are NOT production-ready:

- **No authentication** — API endpoints are open
- **No rate limiting** — Vulnerable to DoS attacks
- **No encryption at rest** — Data stored in plaintext
- **No secrets management** — Config in YAML files
- **Simple event bus** — Not distributed, no message signing

### Recommended for Production

Before deploying to production:

1. Add authentication (OAuth2, API keys)
2. Implement rate limiting
3. Encrypt sensitive data at rest
4. Use secrets management (HashiCorp Vault, AWS Secrets Manager)
5. Sign events with HMAC for integrity
6. Deploy behind reverse proxy (nginx, Traefik)
7. Enable HTTPS/TLS
8. Implement monitoring and alerting

## Best Practices

### For Developers

- Never commit secrets or credentials
- Run `make scan` before every commit
- Use environment variables for sensitive config
- Keep dependencies up to date
- Review third-party code before integration

### For Users

- Run AegisTwin in isolated environments
- Restrict network access to API endpoints
- Use read-only filesystem mounts where possible
- Monitor audit logs for suspicious activity
- Regularly update to latest version

## Security Checklist

Before deploying AegisTwin:

- [ ] Authentication enabled
- [ ] HTTPS/TLS configured
- [ ] Rate limiting implemented
- [ ] Secrets externalized
- [ ] Logging and monitoring configured
- [ ] Firewall rules in place
- [ ] Regular backup schedule
- [ ] Incident response plan documented

## Compliance

### Data Privacy

AegisTwin is designed to respect data privacy:

- No telemetry sent to external servers
- All data processing happens locally
- PII scanner prevents accidental data leaks
- Synthetic fixtures for all demos

### Export Control

AegisTwin does not contain:

- Encryption algorithms (uses OS-level crypto)
- Controlled technology under ITAR
- Export-restricted components

## Acknowledgments

We thank security researchers who responsibly disclose vulnerabilities. Public acknowledgment (with permission) will be included in security advisories.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Last Updated:** 2026-01-06
