---
name: chi26
version: 1.0.0
description: |
  CHI 2026 paper recommender. Searches 1700+ papers, posters, workshops, and demos
  from ACM CHI 2026 (Barcelona, April 13-17) and recommends content based on
  research interests. Use when the user asks about CHI papers, wants recommendations,
  or needs to plan their conference schedule.
allowed-tools:
  - Bash
  - Read
---

# CHI 2026 Paper Recommender

You have access to the full CHI 2026 program data.

**Important:** Resolve paths relative to this skill's base directory. Use this pattern to find the skill directory:
```bash
SKILL_DIR="$(dirname "$(find ~/.claude/skills/chi26 -name SKILL.md 2>/dev/null || find . -name SKILL.md 2>/dev/null | head -1)")"
```
Or if installed via `npx skills add`, find it wherever the agent placed it:
```bash
SKILL_DIR="$(find ~ -path "*/chi26/SKILL.md" -not -path "*/node_modules/*" 2>/dev/null | head -1 | xargs dirname)"
```
Data file: `$SKILL_DIR/CHI_2026_program.json`
Search script: `$SKILL_DIR/search.py`

## Data Schema

The JSON contains these key arrays:

- **contents** (2780 items): Papers, posters, demos, workshops, meetups, panels
  - `id`, `title`, `abstract`, `trackId`, `typeId`, `sessionIds`, `authors[]`
  - Each author has `personId` and `affiliations[]` (institution, city, country)
  - `addons.doi.url` links to ACM Digital Library
- **sessions** (448): Grouped presentations with time/room
  - `id`, `name`, `timeSlotId`, `roomId`, `contentIds[]`, `chairIds[]`
- **people** (9757): Author/presenter directory
  - `id`, `firstName`, `lastName`, `affiliations[]`
- **timeSlots** (39): Schedule slots with `startDate`/`endDate` (epoch ms, timezone Europe/Brussels UTC+2)
- **rooms** (43): Venue rooms with `name`
- **tracks**: Content categories by ID:
  - 13833 = Papers (1702), 13843 = Posters (789), 13834 = Workshops (69)
  - 13842 = Interactive Demos (67), 13848 = Journals (36), 13832 = Meet-Ups (32)
  - 13844 = Panels (8), 13836 = Keynotes (4), 13847 = Student Research Competition (12)
  - 13868 = Awards

## How to Recommend

When the user provides research interests or a query:

1. **Load and search the data** using a Python script via Bash. Match against titles and abstracts using keyword/phrase matching. Example:

```bash
SKILL_DIR="$(dirname "$(find ~ -path "*/chi26/SKILL.md" -not -path "*/node_modules/*" 2>/dev/null | head -1)")"
python3 "$SKILL_DIR/search.py" "your query here"
```

If the search script doesn't exist yet or needs a custom query, write inline Python:

```python
import json, re

import os; SKILL_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ.get('SKILL_DIR', '.')
with open(os.path.join(SKILL_DIR, "CHI_2026_program.json")) as f:
    data = json.load(f)

people = {p["id"]: p for p in data["people"]}
timeslots = {t["id"]: t for t in data["timeSlots"]}
sessions_map = {s["id"]: s for s in data["sessions"]}
rooms = {r["id"]: r for r in data["rooms"]}

# Search terms - adapt these based on user query
terms = ["mixed reality", "tangible", "fabrication"]

results = []
for c in data["contents"]:
    text = (c["title"] + " " + c.get("abstract", "")).lower()
    score = sum(1 for t in terms if t.lower() in text)
    if score > 0:
        results.append((score, c))

results.sort(key=lambda x: -x[0])

for score, c in results[:20]:
    authors = ", ".join(
        f'{people[a["personId"]]["firstName"]} {people[a["personId"]]["lastName"]}'
        for a in c["authors"] if a["personId"] in people
    )
    # Get session time
    session_info = ""
    for sid in c.get("sessionIds", []):
        s = sessions_map.get(sid)
        if s and s.get("timeSlotId"):
            ts = timeslots.get(s["timeSlotId"])
            if ts:
                from datetime import datetime, timezone, timedelta
                dt = datetime.fromtimestamp(ts["startDate"]/1000, tz=timezone(timedelta(hours=2)))
                room = rooms.get(s.get("roomId"), {}).get("name", "")
                session_info = f" | {dt.strftime('%a %b %d %H:%M')} @ {room}"
    doi = c.get("addons", {}).get("doi", {}).get("url", "")
    print(f"[{score}] {c['title']}")
    print(f"    Authors: {authors[:120]}")
    print(f"    {doi}{session_info}")
    print()
```

2. **Present results** in a clear table or list format with:
   - Paper title
   - Authors (first 3 + "et al." if more)
   - Session day/time and room (converted from epoch ms, UTC+2)
   - ACM DL link (doi)
   - A one-line summary of why it matches their interest (from the abstract)

3. **Support these query types:**
   - Topic search: "papers about accessibility", "XR interaction papers"
   - Author search: "papers by [name]", "what is [name] presenting"
   - Schedule planning: "what's on Tuesday afternoon", "sessions in Room X"
   - Session browse: "list all sessions on fabrication"
   - Affiliation search: "papers from MIT", "who from Stanford is presenting"
   - Combined: "accessibility papers on Wednesday morning"

4. **When recommending based on broad interests**, group results by sub-theme and highlight any best paper awards (check `recognitionIds`).

5. **Conference is April 13-17, 2026 in Barcelona** (CCIB). Times are in Europe/Brussels (UTC+2).
