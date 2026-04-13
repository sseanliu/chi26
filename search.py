#!/usr/bin/env python3
"""CHI 2026 program search. Usage: python3 search.py <query> [--type papers|posters|demos|workshops|all] [--day mon|tue|wed|thu|fri] [--author name] [--affiliation name] [--limit N]"""
import json, sys, os, re
from datetime import datetime, timezone, timedelta

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CHI_2026_program.json")
TZ = timezone(timedelta(hours=2))

TRACK_NAMES = {
    13833: "Paper", 13843: "Poster", 13834: "Workshop", 13842: "Demo",
    13848: "Journal", 13832: "Meet-Up", 13844: "Panel", 13836: "Keynote",
    13847: "SRC", 13868: "Award", 13827: "Other",
    13845: "Mentoring", 13846: "Mentoring"
}
TRACK_FILTER = {
    "papers": [13833], "posters": [13843], "demos": [13842],
    "workshops": [13834], "journals": [13848], "panels": [13844],
    "keynotes": [13836], "all": list(TRACK_NAMES.keys())
}
DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4}
CONF_START = datetime(2026, 4, 13, tzinfo=TZ)  # Monday

def load():
    with open(DATA) as f:
        return json.load(f)

def main():
    args = sys.argv[1:]
    query_terms, content_type, day_filter, author_q, affil_q, limit = [], "all", None, None, None, 25

    i = 0
    while i < len(args):
        if args[i] == "--type" and i+1 < len(args):
            content_type = args[i+1].lower(); i += 2
        elif args[i] == "--day" and i+1 < len(args):
            day_filter = args[i+1].lower()[:3]; i += 2
        elif args[i] == "--author" and i+1 < len(args):
            author_q = args[i+1].lower(); i += 2
        elif args[i] == "--affiliation" and i+1 < len(args):
            affil_q = args[i+1].lower(); i += 2
        elif args[i] == "--limit" and i+1 < len(args):
            limit = int(args[i+1]); i += 2
        else:
            query_terms.append(args[i].lower()); i += 1

    data = load()
    people = {p["id"]: p for p in data["people"]}
    timeslots = {t["id"]: t for t in data["timeSlots"]}
    sessions_map = {s["id"]: s for s in data["sessions"]}
    rooms = {r["id"]: r for r in data["rooms"]}

    allowed_tracks = TRACK_FILTER.get(content_type, TRACK_FILTER["all"])

    results = []
    for c in data["contents"]:
        if c["trackId"] not in allowed_tracks:
            continue
        if c.get("isBreak"):
            continue

        # Author filter
        if author_q:
            author_names = []
            for a in c.get("authors", []):
                p = people.get(a["personId"])
                if p:
                    author_names.append(f'{p["firstName"]} {p["lastName"]}'.lower())
            if not any(author_q in name for name in author_names):
                continue

        # Affiliation filter
        if affil_q:
            found = False
            for a in c.get("authors", []):
                for aff in a.get("affiliations", []):
                    if affil_q in aff.get("institution", "").lower():
                        found = True; break
                if found: break
            if not found:
                continue

        # Day filter
        if day_filter and day_filter in DAY_MAP:
            target_day = DAY_MAP[day_filter]
            in_day = False
            for sid in c.get("sessionIds", []) + c.get("eventIds", []):
                s = sessions_map.get(sid)
                if s and s.get("timeSlotId"):
                    ts = timeslots.get(s["timeSlotId"])
                    if ts:
                        dt = datetime.fromtimestamp(ts["startDate"]/1000, tz=TZ)
                        if (dt.date() - CONF_START.date()).days == target_day:
                            in_day = True; break
            if not in_day:
                continue

        # Score by query terms
        text = (c["title"] + " " + c.get("abstract", "")).lower()
        if query_terms:
            # Support multi-word phrases joined by query_terms
            full_query = " ".join(query_terms)
            # Try full phrase first, then individual words
            score = 0
            if full_query in text:
                score += 5
            # Title matches worth more
            title_lower = c["title"].lower()
            if full_query in title_lower:
                score += 10
            for t in query_terms:
                if t in title_lower:
                    score += 3
                if t in text:
                    score += 1
            if score == 0:
                continue
        else:
            score = 1  # no query = show all (filtered by other criteria)

        results.append((score, c))

    results.sort(key=lambda x: -x[0])

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results (showing top {min(limit, len(results))}):\n")

    for score, c in results[:limit]:
        track = TRACK_NAMES.get(c["trackId"], "?")
        # Authors
        author_list = []
        for a in c.get("authors", [])[:4]:
            p = people.get(a["personId"])
            if p:
                author_list.append(f'{p["firstName"]} {p["lastName"]}')
        authors_str = ", ".join(author_list)
        if len(c.get("authors", [])) > 4:
            authors_str += " et al."

        # Session time
        session_info = ""
        for sid in c.get("sessionIds", []) + c.get("eventIds", []):
            s = sessions_map.get(sid)
            if s and s.get("timeSlotId"):
                ts = timeslots.get(s["timeSlotId"])
                if ts:
                    dt = datetime.fromtimestamp(ts["startDate"]/1000, tz=TZ)
                    room = rooms.get(s.get("roomId"), {}).get("name", "")
                    session_info = f"{dt.strftime('%a %b %d %H:%M')} @ {room}"
                    if s.get("name"):
                        session_info += f" ({s['name']})"
                    break

        doi = c.get("addons", {}).get("doi", {}).get("url", "")

        print(f"[{track}] {c['title']}")
        print(f"  Authors: {authors_str}")
        if session_info:
            print(f"  When: {session_info}")
        if doi:
            print(f"  DOI: {doi}")
        print()

if __name__ == "__main__":
    main()
