# scalecraft-outreach

Draft personalized cold emails from your lead list, with built-in templates
and a send-state tracker so nobody gets messaged twice. Part of the ScaleCraft
lead pipeline: **hunter** (clean raw lists) → **scorer** (rank them) →
**outreach** (draft emails).

Offline, stdlib-only, single file.

## Templates

- `intro` — first touch, references their website situation
- `followup` — gentle nudge
- `automation` — pitches automation angle for businesses doing things by hand

Personalization picks the observation line from the lead's website field:
no site → "you don't have a website yet", social-only → "you're on social
but don't have your own site", has a site → "your current site could be
doing a lot more".

## Usage

```
python scalecraft-outreach.py --in leads.csv
python scalecraft-outreach.py --in leads.csv --template automation
python scalecraft-outreach.py --in leads.csv --status state.json --out drafts.json
```

`--status` records drafted names; reruns skip them. Safe to cron.

## Tests

```
python -m unittest test_outreach
```

MIT
