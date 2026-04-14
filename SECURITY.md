# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `main`  | Yes       |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, e-mail the maintainer directly or use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability).

Include:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Any suggested fix (optional)

We aim to acknowledge reports within **72 hours** and publish a fix within **14 days** for critical issues.

## Scope

Issues in scope:

- API key exposure or insecure handling of `st.secrets` / environment variables
- Dependencies with known CVEs (`pip audit`)
- XSS or injection via user-supplied ticker input
- Unintended data exfiltration

Out of scope:

- Accuracy of financial data from Yahoo Finance (a third-party service)
- Performance issues
- Feature requests
