#!/usr/bin/env python3
"""Convert markdown draft(s) to Word (.docx) and deliver them to the founder — cross-platform.

Every FounderHive agent uses this so emails/outputs are readable .docx (not raw .md). Delivery method is
chosen in config.yaml (or env), so this works on macOS, Windows and Linux:

  delivery.method:
    save     -> (default, zero setup) write the .docx + a note into ./outbox/<date>/. You read the folder.
    smtp     -> email via SMTP (any provider). Host/port in config; SMTP_USER + SMTP_APP_PASSWORD in ENV.
    mail_app -> macOS only: send through the Apple Mail app (no password stored).

Usage:
  python3 tools/deliver.py --subject "..." --body "..." --md file.md [more.md ...] [--to you@co.com]
"""
import argparse, os, re, sys, shutil, subprocess, smtplib, mimetypes, datetime
from pathlib import Path
from email.message import EmailMessage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def read_config():
    """Minimal read of the delivery block + founder.email from config.yaml (no yaml dependency)."""
    cfg = {"method": "save", "to": "", "smtp_host": "smtp.gmail.com", "smtp_port": "587", "outbox": "outbox"}
    f = ROOT / "config.yaml"
    if f.exists():
        section = None
        for line in f.read_text().splitlines():
            if re.match(r"^\S", line):  # top-level key resets section
                section = line.split(":", 1)[0].strip()
            m = re.match(r"^\s+([a-z_]+):\s*(.+?)\s*$", line)
            if not m:
                continue
            k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
            if section == "delivery" and k in cfg:
                cfg[k] = v
            if section == "founder" and k == "email" and not cfg["to"]:
                cfg["to"] = v
    # env overrides
    cfg["method"] = os.environ.get("DELIVERY_METHOD", cfg["method"])
    cfg["to"] = os.environ.get("MAIL_TO", cfg["to"])
    return cfg

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
    to = cfg["to"] or user
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
    cmd = [sys.executable, str(HERE / "send_mail_macos.py"), "--subject", subject, "--body", body]
    if cfg["to"]: cmd += ["--to", cfg["to"]]
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
    if args.to: cfg["to"] = args.to
    files = to_docx(args.md) + list(args.attach)
    {"save": deliver_save, "smtp": deliver_smtp, "mail_app": deliver_mail_app}.get(cfg["method"], deliver_save)(
        cfg, args.subject, args.body, files)

if __name__ == "__main__":
    main()
