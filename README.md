# chi26

CHI 2026 paper recommender skill for AI agents (Claude Code, Cursor, GitHub Copilot, etc.)

Search and get recommendations from 1700+ papers, 789 posters, 69 workshops, and 67 demos from ACM CHI 2026 in Barcelona (April 13-17, 2026).

## Install

```bash
npx skills add sseanliu/chi26
```

## Usage

After installing, just ask your agent "recommend CHI papers on [topic]" or type `/chi26`.

## What it does

Once installed, your AI agent can:

- **Topic search**: "find CHI papers about accessibility"
- **Author search**: "what is Ryo Suzuki presenting at CHI?"
- **Schedule planning**: "what's on Tuesday afternoon?"
- **Affiliation search**: "papers from Stanford"
- **Combined queries**: "XR interaction papers on Wednesday morning"

## Data

Program data exported from [programs.sigchi.org/chi/2026](https://programs.sigchi.org/chi/2026).

Content licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## Files

- `SKILL.md` — Skill definition (agent instructions)
- `search.py` — Fast keyword search across titles and abstracts
- `CHI_2026_program.json` — Full program data (2780 content items, 9757 authors, 448 sessions)
