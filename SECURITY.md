# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (master) | yes |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report them to: lhk@gni.re.kr

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We will respond within 48 hours and work with you to resolve it before public disclosure.

## Security considerations for self-hosting

agentops is designed for **local or private network use**. If you expose the API server to the internet:

1. Add authentication (the server currently has none)
2. Use HTTPS (put a reverse proxy like Caddy or nginx in front)
3. Set `OPENAI_API_KEY` in `.env` rather than hardcoding
4. Review `wiki/` contents before making the repo public — it may contain sensitive notes
