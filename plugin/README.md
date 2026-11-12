# FounderHive plugin — generated, do not edit by hand

Everything in this folder is **generated** from the canonical sources at the repo root
(`.claude/agents/`, `.claude/commands/`, `tools/`, and the context/gtm/content/scheduling templates).

To change an agent, command or tool, edit the source at the repo root and regenerate:

```bash
python3 tools/build-plugin.py
```

Then validate:

```bash
claude plugin validate ./plugin
claude plugin validate ./
```

See [`tools/build-plugin.py`](../tools/build-plugin.py) for what gets copied and which paths are rewritten
(tool and agent references are pointed at `${CLAUDE_PLUGIN_ROOT}` so they resolve inside the installed
plugin). Users install this via the marketplace — see the main [README](../README.md#install).
