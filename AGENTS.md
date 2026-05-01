# Backtest Agent Guide

## Language Contract

- Internal agent instructions, reusable skill docs, and reusable error/solution entries are written in English.
- User-facing chat with Enes must be Turkish unless Enes explicitly asks for another language.

## Shared Skills and Solution Memory

- For local video content reading, use `/Users/enes/.codex/skills/local-video-content-reader`.
- Never summarize videos from filenames alone; use actual video content through transcript, frame OCR, or manual frame inspection.
- Before debugging a recurring or specific error, search `/Users/enes/.codex/skills/solution-history/references/solution-log.md`.
- If a new reusable fix is discovered and verified, append an English entry to that solution log.
- Do not record secrets, tokens, private credentials, or huge logs in solution history.
