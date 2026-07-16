# Scheduling your agents (recurring runs)

FounderHive's real value is agents running on a cadence and delivering to you automatically. Schedules
aren't files in this repo — you create them once in your Claude environment. Two ways:

## Option A — Claude app "Scheduled" tasks (easiest)
In the Claude app, open the **Scheduled** section → new task. Paste one of the prompts below (replace
`{PROJECT_DIR}` with the absolute path to this folder). Pick the cadence from the table. Tip: hit **Run
now** once to pre-approve tool permissions so future runs don't pause.

> Note: local scheduled tasks run while the app is open, and catch up on next launch if it was closed.

## Option B — cron (fully unattended, if you run Claude Code headless)
Add a crontab line per agent that invokes your Claude CLI against `{PROJECT_DIR}` with the task prompt.
Cadence is the cron expression in the table. (Advanced — depends on your CLI setup.)

## Recommended cadence
| Agent | Cadence | Cron |
|---|---|---|
| Jason (GTM) | Weekly, Mon 08:00 | `0 8 * * 1` |
| Dawn (content) | ~every 3 weeks (self-gated), Mon 09:00 | `0 9 * * 1` |
| Honey (chief of staff) | Weekly, Mon 10:00 (after the others) | `0 10 * * 1` |
| Deap (product) | Weekly, Wed 09:00 | `0 9 * * 3` |
| Tarik (customer success) | Weekly, Thu 09:00 | `0 9 * * 4` |
| Simon (investor relations) | Monthly, 1st 09:00 | `0 9 1 * *` |
| James (CTO) | Weekly, Fri 09:00 (architecture watch) | `0 9 * * 5` |
| Nora (people/legal/finance) | Monthly, 28th 09:00 | `0 9 28 * *` |

## Paste-ready task prompt (template — one per agent)
Replace `{PROJECT_DIR}` and `{AGENT}` (honey/jason/dawn/tarik/deap/simon/james/nora):

```
Run FounderHive's scheduled beat as the {AGENT} agent.
PROJECT DIRECTORY: {PROJECT_DIR} — work relative to it.
1. Read .claude/agents/{AGENT}.md and config.yaml + company-context/*, and follow them exactly.
2. Do this agent's recurring work (see its definition), grounded in the source_folder; never act
   externally or contact anyone but the founder; draft only.
3. Deliver to the founder as Word:
   python3 tools/deliver.py --subject "FounderHive · {AGENT} — <YYYY-MM-DD>" --md <the artefact>.md --body "<short summary + what needs the founder's decision>"
   (deliver.py converts to .docx and uses the delivery method in config.yaml; if nothing material this
   run, update the workspace quietly and skip delivery.)
```

## Weekly-gated cadences (Dawn's ~3-week pattern)
Cron can't express "every 3 weeks". For that, schedule weekly and have the task check its own log/calendar
first and stop early if it isn't due yet (e.g. Dawn reads `content/content-calendar.md` and exits if <~20
days since the last delivery). See Dawn's definition for the pattern.
