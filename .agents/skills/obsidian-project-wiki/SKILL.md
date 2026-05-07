---
name: obsidian-project-wiki
description: Use when maintaining the Backtest project's Obsidian-compatible project wiki in docs/wiki, querying architecture memory before coding, ingesting recent repository changes into linked notes, or linting stale wiki links without changing the codebase structure.
metadata:
  short-description: Maintain docs/wiki as an Obsidian project memory
---

# Obsidian Project Wiki

This skill keeps `/Users/enes/AgentWorkspace/Backtest/docs/wiki` as a local,
human-readable project memory for agents and Enes.

## Ground Rules

- Do not move or rename production code while maintaining the wiki.
- Treat `docs/wiki/index.md` as the entry point.
- Prefer short linked notes over one giant document.
- Use Obsidian wiki links: `[[note-name]]` or `[[folder/note-name]]`.
- Keep notes factual and source them to repository paths or existing docs.
- If code changes, update only the related notes; do not rebuild the whole wiki unless asked.
- Never paste secrets, tokens, large logs, or copyrighted long transcripts into the wiki.

## Operations

### Query

Before broad code exploration:

1. Read `docs/wiki/index.md`.
2. Follow the smallest relevant map note under `docs/wiki/01-maps/`.
3. Only then inspect repository files that are directly relevant.

### Ingest

After a meaningful code or docs change:

1. Check `git diff --name-only`.
2. Map changed files to the closest note in `docs/wiki/04-modules/` or `docs/wiki/01-maps/`.
3. Add concise facts: what changed, why it matters, and where the source file is.
4. Add or update links to related notes.

### Lint

When asked to clean the wiki:

1. Search for missing wiki targets with `rg "\\[\\[" docs/wiki`.
2. Check that each linked target exists or intentionally points to a future note.
3. Remove stale claims that contradict current source files.
4. Keep archive/history notes rather than deleting useful decisions.

## Note Template

```markdown
# Title

## Purpose
One or two sentences.

## Source Files
- `path/to/file.py`

## Current Facts
- Fact grounded in source.

## Related
- [[other-note]]
```

