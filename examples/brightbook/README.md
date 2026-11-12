# Example company — Brightbook

A fully filled-in **example startup** so you can try FounderHive in 2 minutes, before configuring your own.
**Brightbook** is a (fictional) bookkeeping app for freelancers — deliberately a plain, non-AI business so
the agents' value is obvious for any kind of founder.

## Try it (2 minutes)
From the repo root:
```bash
python3 tools/demo.py          # loads Brightbook (backs up your own files first)
```
Then, in Claude Code, call a teammate:
- `/max challenge my pricing` — the Co-Founder stress-tests Brightbook's £9/mo model
- `/dawn draft a blog on freelancer tax` — in Sam's voice
- `/jason find partnership targets` — accountants & freelancer communities
- `/simon draft a pre-seed one-pager`

Everything is local (delivery is `save` → drafts land in `outbox/`). Nothing is emailed.

When you're done:
```bash
python3 tools/demo.py --restore   # puts your own config + context back
```

## What's inside
`config.yaml` (Sam Rivera / Brightbook) · a filled `company-context/` (bio, voice, overview, knowledge-base,
customer-evidence) · `gtm/` (ICP, messaging, outreach voice) · `content/` (calendar, ideas) · and
`source/` — the "company folder" the agents read (one-pager, pricing, roadmap, customer notes).

Use it as a **reference** for what good context looks like when you fill in your own.
