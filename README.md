# FounderHive — a founder operating system of AI agents

FounderHive gives a solo/early founder a small **team of AI agents** — a chief of staff, a GTM lead, a
content lead, customer success, product, investor relations, and a CTO — that do real work and hand it to
you **for approval**. It's built on [Claude Code](https://claude.com/claude-code): each agent is a
markdown definition; your company knowledge is markdown + your existing files; nothing is a black box.

**The core idea:** proactive founder work (thought leadership, pipeline, investor prep) always loses to
whatever's urgent. The agents *collapse the activation energy* — they produce the 80% draft so the only
thing left is your quick edit. **They draft; you decide.** No agent sends an email, posts, publishes,
commits code, or acts externally. The only thing they ever send is a draft **to you**.

## The agents (`.claude/agents/`)
| Agent | Role | Produces |
|---|---|---|
| **Honey** | Chief of Staff | Daily/weekly founder briefs, priorities, blockers |
| **Jason** | GTM | Target lists, outreach drafts, market signals, competitor watch, weekly GTM brief |
| **Dawn** | Content | Blog/LinkedIn drafts in your voice |
| **Tarik** | Customer Success | Meeting briefs, interview kits + synthesis, follow-ups, action trackers |
| **Deap** | Product | PRDs, user stories, roadmap |
| **Simon** | Investor Relations | One-pager, data-room checklist, traction narrative, monthly investor update |
| **James** | CTO (agent) | Architecture notes, feasibility, technical plans |
| **Nora** | People, Legal & Finance | Job specs, contracts/IP/equity tracking, weekly bookkeeping, runway, accountant/lawyer prep |
| **Max** | Co-Founder (challenger) | Reads your idea docs and stress-tests them — market, pricing, competition, sales friction, GTM, tech complexity, AI governance, ethics |

## Setup — the easy way
1. **Prereqs:** Claude Code + Python 3.11+. Install helpers: `pip install -r requirements.txt`.
2. **Run the setup agent** — open Claude Code in this folder and say *"Use the setup agent."* It interviews
   you and fills `config.yaml` + `company-context/*` (and GTM basics), reading your company folder to map
   material. That's the whole setup, guided.
3. **Check readiness:** `python3 tools/preflight.py` — tells you if anything's still a placeholder.

### Setup — the manual way (if you prefer)
Fill `config.yaml` (name, email, company one-liner(s), `source_folder`, and a **delivery method**), then the
`company-context/` templates — especially `founder-bio.md` and `founder-voice.md` (paste 2–4 real writing
samples), plus `company-overview.md`, `knowledge-base.md` (map your folder to the agents) and
`customer-evidence.md`. Then `gtm/` and `content/` as needed. Run `preflight.py` when done.

### Delivery — works on any OS (set in `config.yaml → delivery.method`)
- **`save`** (default, zero setup): drafts land as Word docs in `outbox/<date>/` — just read the folder.
- **`smtp`**: emails via any provider. Put `SMTP_USER` + `SMTP_APP_PASSWORD` in your **environment** (never
  in the file); set host/port in config.
- **`mail_app`** (macOS only): sends via the Apple Mail app already signed in — no password stored.

## Using it
- Ask, e.g. *"Use the Dawn agent to draft a blog on X"* or *"Use Jason to build a target list for segment Y."*
  The agent reads `config.yaml` + `company-context/`, drafts, converts to **Word (.docx)**, and delivers it.
- **Recurring runs:** see [`scheduling/SCHEDULING.md`](scheduling/SCHEDULING.md) for recommended cadences
  and paste-ready task prompts (Dawn ~3-weekly, Jason weekly, Honey weekly, etc.).

## Guardrails (built in — safe for classroom / shared use)

Every agent carries a **"Shared guardrails"** block (see any file in `.claude/agents/`), and the key rule is
enforced in code so it can't be talked around. In full:

- **Email only ever reaches the configured user — enforced in code.** The delivery tools
  (`tools/deliver.py`, `tools/send_mail_macos.py`) confirm the recipient equals the address in
  `config.yaml → founder.email` and **hard-refuse any other recipient** (exit 1, no override flag). An agent
  — or a prompt trying to make one — cannot email a customer, a classmate, or the outside world. "The user"
  is whoever set that address; each person's copy can only email **their own** address. The default delivery
  method is **`save`**, so out of the box nothing is emailed at all — drafts just land in `outbox/`.
- **Draft, never act.** No agent publishes, posts, commits code, buys anything, moves money, creates or logs
  into accounts, or enters credentials/payment details. It prepares drafts for your approval — and for
  legal/finance matters, for a qualified professional. Nothing irreversible happens without a human.
- **Stays inside the project.** Agents write only within the FounderHive folder and treat your `source_folder`
  and any customer material as **read-only** — they never move, rename, edit or delete your files.
- **Lawful, cited research.** Every agent follows
  [`company-context/research-and-sourcing-policy.md`](company-context/research-and-sourcing-policy.md):
  lawful public sources only (never bypass paywalls/logins/robots/CAPTCHAs), a cited source URL for every
  web-sourced claim, brief attributed quotes only (no substantial copyrighted text), and uncited claims
  marked `[UNVERIFIED]`.
- **Content is data, not instructions.** Instructions embedded in files or web pages are ignored
  (prompt-injection) — treated as information to evaluate, never commands to follow.
- **No impersonation or deception, no invented facts.** No content posing as a real person/organisation, no
  fake reviews/credentials; agents ground claims in your real material, flag what needs your judgement, and
  anonymise customers/partners in anything external. Secrets (passwords, API keys) stay in the environment,
  never in files.
- **No shell access.** No agent carries the `Bash` tool — none can run arbitrary commands on the machine.
  (Re-add `Bash` to a single agent's `tools:` line only if you deliberately need it, e.g. git/spreadsheet
  parsing.)

**For educators:** the safest classroom setup is the default and is already how the kit ships — no agent has
shell access; `delivery.method: save` means no email is sent at all (drafts land in `outbox/`); each student
sets `founder.email` to **their own** address; and students run agents **on demand** (scheduled tasks consume
API usage). Nothing an agent does leaves the student's machine unless they deliberately configure email.

## ⚠️ Keep private (don't share/commit with real data)
`config.yaml` (your email), `company-context/customer-evidence.md`, your filled `founder-bio.md`, any real
prospect/customer data, `gtm/outreach-drafts/`, `gtm/weekly-brief/`, `content/drafts/`. The included
`.gitignore` excludes the common ones — but **review before pushing anywhere.** Share the *empty templates*,
never your filled-in copies.

## License
[MIT](LICENSE) — free to use, modify and share. No warranty; you're responsible for what your agents draft
and what you send.

---
*FounderHive was pressure-tested before it was built: the winning shape is AI agents over markdown that
draft for a human — not a bespoke app, and not autonomy. Keep it that way.*
