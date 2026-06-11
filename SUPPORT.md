# Getting Help

## Documentation
- [README](README.md) — installation, features, architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute
- [examples/](examples/) — real-world usage patterns

## Community
- **GitHub Issues** — bugs and feature requests
- **GitHub Discussions** — questions and ideas

## Quick troubleshooting

**Dashboard doesn't load after `docker compose up`**
```bash
docker compose logs api   # check for errors
```

**`update_status.py` says "unknown agent ID"**
```bash
python -c "import json; print(list(json.load(open('agent_status.json'))['agents'].keys()))"
```

**Wiki notes not appearing in MoC**
```bash
python scripts/wiki_cleanup.py   # auto-register all notes
```
