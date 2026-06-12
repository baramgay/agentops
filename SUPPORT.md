# Support

## Getting Help

### Documentation

- [README](README.md) — Quick start and overview
- [CONTRIBUTING](CONTRIBUTING.md) — How to contribute
- [AGENT_CREATION_GUIDE](AGENT_CREATION_GUIDE.md) — Creating new agents
- [SYNC_GUIDE](SYNC_GUIDE.md) — Multi-device synchronization

### GitHub Issues

For bugs, feature requests, and questions, please use the [GitHub Issues](https://github.com/baramgay/agent/issues) tracker.

When filing a bug report, please include:

1. Your operating system and version
2. Python version (`python --version`)
3. Steps to reproduce the issue
4. Expected vs. actual behavior
5. Relevant log output or error messages

### Common Issues

**Dashboard not updating**
- Run `python scripts/build_html.py` to regenerate `index.html`
- Check that `agent_status.json` is valid JSON

**Status update script fails**
- Verify Python 3.8+ is installed
- Check that `agent_status.json` exists in the repo root
- Run `python scripts/update_status.py --help` for usage

**Wiki notes not appearing in MoC**
- Ensure notes are saved under `wiki/notes/<type>/` (not the root `wiki/notes/`)
- Verify the `domain:` field in the note frontmatter matches a valid MoC name

### Community

This project is maintained as an open-source tool. Community contributions and feedback are welcome via GitHub.
