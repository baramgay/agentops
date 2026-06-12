# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in agentops, please report it responsibly.

**Do not** open a public GitHub issue for security vulnerabilities.

Instead, please email the maintainer directly or use GitHub's private vulnerability reporting feature.

We will acknowledge your report within 48 hours and aim to resolve confirmed vulnerabilities within 14 days.

## Scope

This project manages local agent configuration files and scripts. Key areas of concern include:

- Scripts that execute system commands (`scripts/update_status.py`, etc.)
- Configuration files that may contain sensitive data
- Any file that reads/writes to the filesystem

## Best Practices for Users

- Do not store API keys or credentials in `config.local.json` if committing to a shared repo
- Review agent role definitions before deploying to shared environments
- Use environment variables for sensitive configuration values
