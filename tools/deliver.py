#!/usr/bin/env python3
"""Convert markdown draft(s) to Word (.docx) and deliver them to the founder — cross-platform.

Every FounderHive agent uses this so emails/outputs are readable .docx (not raw .md). Delivery method is
chosen in config.yaml (or env), so this works on macOS, Windows and Linux:

  delivery.method:
    save     -> (default, zero setup) write the .docx + a note into ./outbox/<date>/. You read the folder.
    smtp     -> email via SMTP (any provider). Host/port in config; SMTP_USER + SMTP_APP_PASSWORD in ENV.
    mail_app -> macOS only: send through the Apple Mail app (no password stored).

SAFETY GUARDRAIL (hard, cannot be overridden by an agent or a prompt):
  FounderHive agents may ONLY ever email the founder themselves. This tool confirms the recipient equals
  the configured founder email (config.yaml → founder.email / delivery.to, or the MAIL_TO env var) and
  REFUSES to send to anyone else. To change the owner, a human edits config.yaml. There is no flag to
  disable this.

Usage:
  python3 tools/deliver.py --subject "..." --body "..." --md file.md [more.md ...] [--to founder@co.com]
"""
import argparse, os, re, sys, shutil, subprocess, smtplib, mimetypes, datetime
from pathlib import Path
from email.message import EmailMessage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def read_config():
    cfg = {"method": "save", "to": "", "smtp_host": "smtp.gmail.com", "smtp_port": "587", "outbox": "outbox"}
    f = ROOT / "config.yaml"
    if f.exists():
        section = None
        for line in f.read_text().splitlines():
            if re.match(r"^\S", line):
                section = line.split(":", 1)[0].strip()
            m = re.match(r"^\s+([a-z_]+):\s*(.+?)\s*$", line)
            if not m:
                continue
            k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
            if section == "delivery" and k in cfg:
                cfg[k] = v
            if section == "founder" and k == "email" and not cfg["to"]:
                cfg["to"] = v
    cfg["method"] = os.environ.get("DELIVERY_METHOD", cfg["method"])
    cfg["to"] = os.environ.get("MAIL_TO", cfg["to"])
    return cfg

def _norm(e):
    return (e or "").strip().lower()

def enforce_recipient(requested, allowed):
    """HARD GUARDRAIL: the only permitted recipient is the configured founder. Refuse anything else."""
    a = _norm(allowed)
    r = _norm(requested) or a           # no --to given ⇒ default to the founder
    if not a:
        sys.exit("REFUSED: no founder email configured (config.yaml → founder.email, or MAIL_TO). "
                 "FounderHive agents may only email the founder, so set your own address first.")
    if r != a:
        sys.exit(f"REFUSED: FounderHive agents may only email the founder ({allowed}). "
                 f"Requested recipient '{requested}' is not allowed and will not be contacted. "
                 f"This safety guardrail cannot be overridden; to change the owner, a human edits config.yaml.")
    return a

def to_docx(md_paths):
    out = []
    for md in md_paths:
        p = Path(md)
        if not p.exists():
            print(f"WARN: not found, skipping: {p}", file=sys.stderr); continue
        d = str(p.with_suffix(".docx"))
        r = subprocess.run([sys.executable, str(HERE / "md-to-docx.py"), str(p), d], capture_output=True, text=True)
        out.append(d if r.returncode == 0 else str(p))
    return out

def deliver_save(cfg, subject, body, files):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    dest = ROOT / cfg["outbox"] / stamp
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy2(f, dest / Path(f).name)
    (dest / "_message.txt").write_text(f"To: {cfg['to'] or '(founder)'}\nSubject: {subject}\n\n{body}\n")
    print(f"saved: {dest}  ({len(files)} file(s)) — open your outbox to review.")

def deliver_smtp(cfg, subject, body, files):
    user, pw = os.environ.get("SMTP_USER"), os.environ.get("SMTP_APP_PASSWORD")
    if not user or not pw:
        print("SMTP creds missing (set SMTP_USER + SMTP_APP_PASSWORD env). Falling back to 'save'.", file=sys.stderr)
        return deliver_save(cfg, subject, body, files)
    to = enforce_recipient(cfg["to"], cfg["to"])   # re-assert: founder only
    msg = EmailMessage(); msg["From"], msg["To"], msg["Subject"] = user, to, subject
    msg.set_content(body or "(no body)")
    for f in files:
        ctype, _ = mimetypes.guess_type(f); maintype, subtype = (ctype.split("/", 1) if ctype else ("application", "octet-stream"))
        msg.add_attachment(Path(f).read_bytes(), maintype=maintype, subtype=subtype, filename=Path(f).name)
    with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"])) as s:
        s.starttls(); s.login(user, pw); s.send_message(msg)
    print(f"emailed (smtp): '{subject}' -> {to} ({len(files)} attachment(s))")

def deliver_mail_app(cfg, subject, body, files):
    if sys.platform != "darwin":
        print("mail_app is macOS-only; falling back to 'save'.", file=sys.stderr)
        return deliver_save(cfg, subject, body, files)
    to = enforce_recipient(cfg["to"], cfg["to"])   # re-assert: founder only
    cmd = [sys.executable, str(HERE / "send_mail_macos.py"), "--to", to, "--subject", subject, "--body", body]
    if files: cmd += ["--attach"] + files
    if subprocess.run(cmd).returncode != 0:
        deliver_save(cfg, subject, body, files)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--md", nargs="+", required=True)
    ap.add_argument("--attach", nargs="*", default=[])
    ap.add_argument("--to")
    args = ap.parse_args()
    cfg = read_config()
    # HARD GUARDRAIL: confirm the recipient is the founder (and only the founder) before anything is sent.
    cfg["to"] = enforce_recipient(args.to, cfg["to"])
    files = to_docx(args.md) + list(args.attach)
    {"save": deliver_save, "smtp": deliver_smtp, "mail_app": deliver_mail_app}.get(cfg["method"], deliver_save)(
        cfg, args.subject, args.body, files)

if __name__ == "__main__":
    main()
