#!/usr/bin/env python3
"""ScaleCraft Outreach — draft personalized outreach emails from scored leads.

Reads a leads CSV/JSON (same format the scorer/hunter emit) and renders
personalized cold-email drafts from built-in templates. Writes a drafts file
plus a send-state tracker so follow-ups aren't duplicated. Fully offline,
stdlib-only.

Usage:
    python scalecraft-outreach.py --in leads.csv
    python scalecraft-outreach.py --in leads.csv --template followup --status sent.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import sys

TEMPLATES = {
    "intro": {
        "subject": "Quick question about {name}'s website",
        "body": (
            "Hi {name} team,\n\n"
            "I came across {name}{city_part} and noticed {observation}.\n"
            "I build fast, modern websites and booking/automation systems for local "
            "businesses — things like online booking, quote forms, and Google visibility.\n\n"
            "Worth a 10-minute chat this week?\n\n"
            "— Harman\nScaleCraft"
        ),
    },
    "followup": {
        "subject": "Re: Quick question about {name}'s website",
        "body": (
            "Hi {name} team,\n\n"
            "Following up on my last note — I know running a business leaves zero "
            "spare time. If a better website or simpler bookings would help, I can "
            "show you a live demo built around {name} this week.\n\n"
            "Either way, keep it up.\n\n"
            "— Harman\nScaleCraft"
        ),
    },
    "automation": {
        "subject": "Cutting the busywork at {name}",
        "body": (
            "Hi {name} team,\n\n"
            "Quick one: if your team still handles bookings, quotes or follow-ups "
            "by hand, I build small automations that give small businesses hours "
            "back every week. No new software to learn — it fits what you already do.\n\n"
            "Open to seeing a 5-minute walkthrough?\n\n"
            "— Harman\nScaleCraft"
        ),
    },
}


def render(lead: dict, template: str) -> dict:
    name = (lead.get("name") or "there").strip()
    city = (lead.get("city") or "").strip()
    website = (lead.get("website") or "").strip()
    needs = (lead.get("needs_contact_info") or "").split(",")

    if not website:
        observation = "you don't have a website yet — which usually means customers search and find competitors first"
    elif "facebook" in website or "instagram" in website:
        observation = "you're on social but don't have your own site — the one place customers can always find you"
    else:
        observation = "your current site could be doing a lot more for bookings and quotes"

    t = TEMPLATES[template]
    ctx = {"name": name, "city_part": f" in {city}" if city else "", "observation": observation}
    return {
        "name": name,
        "city": city,
        "email": (lead.get("email") or "").strip(),
        "missing": [m for m in needs if m and m != "needs_contact_info"],
        "subject": t["subject"].format(**ctx),
        "body": t["body"].format(**ctx),
        "template": template,
    }


def load_state(path) -> dict:
    p = pathlib.Path(path)
    if not p.exists():
        return {"sent": [], "drafted": []}
    try:
        state = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:  # empty or corrupt state file starts fresh
        return {"sent": [], "drafted": []}
    state.setdefault("sent", [])
    state.setdefault("drafted", [])
    return state


def save_state(state: dict, path) -> None:
    pathlib.Path(path).write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_leads(path) -> list[dict]:
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        doc = json.loads(text)
        return doc if isinstance(doc, list) else doc.get("leads", [])
    return list(csv.DictReader(io.StringIO(text)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="scalecraft-outreach",
                                     description="Draft personalized outreach emails.")
    parser.add_argument("--in", dest="infile", required=True, help="leads CSV or JSON")
    parser.add_argument("--template", choices=sorted(TEMPLATES), default="intro")
    parser.add_argument("--status", help="state file recording drafted/sent names (skips repeats)")
    parser.add_argument("--out", help="write drafts JSON to file")
    args = parser.parse_args(argv)

    try:
        leads = load_leads(args.infile)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not leads:
        print("error: no leads found", file=sys.stderr)
        return 1

    state = load_state(args.status) if args.status else {"sent": [], "drafted": []}
    drafts, skipped = [], 0
    for lead in leads:
        name = (lead.get("name") or "").strip()
        if name and name in state["drafted"]:
            skipped += 1
            continue
        drafts.append(render(lead, args.template))
        if name:
            state["drafted"].append(name)

    if args.status:
        save_state(state, args.status)

    output = json.dumps({"template": args.template, "count": len(drafts), "drafts": drafts}, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(output, encoding="utf-8")
        print(f"wrote {len(drafts)} drafts to {args.out} ({skipped} already drafted, skipped)")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
