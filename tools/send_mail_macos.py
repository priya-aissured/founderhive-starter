#!/usr/bin/env python3
# FounderHive · created by Priya Lakshmi (AISSURED) · https://github.com/priya-aissured/founderhive-starter · MIT
"""Send an email (with optional attachment) via the macOS Mail app — NO password stored.

Drives Apple Mail (already signed into your account) through AppleScript. FounderHive agents use this to
deliver drafts to you for approval. First run triggers a one-time macOS prompt: "<app> wants to control
Mail" → click OK. Requires Mail.app configured with an account that can send as the From address.

SAFETY GUARDRAIL (hard): will ONLY send to the configured founder (config.yaml → founder.email /
delivery.to, or the MAIL_TO env var). Any other recipient is refused. This mirrors the check in deliver.py
so the rule holds even if this script is called directly.

Usage:
  python3 tools/send_mail_macos.py --to founder@co.com --subject "..." --body "..." [--attach f.docx ...]
"""
import argparse, subprocess, sys, tempfile, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def founder_email():
    """Resolve the one permitted recipient: MAIL_TO env, else config.yaml delivery.to / founder.email."""
    if os.environ.get("MAIL_TO"):
        return os.environ["MAIL_TO"]
    f = ROOT / "config.yaml"
    to, section = "", None
    if f.exists():
        for line in f.read_text().splitlines():
            if re.match(r"^\S", line):
                section = line.split(":", 1)[0].strip()
            m = re.match(r"^\s+([a-z_]+):\s*(.+?)\s*$", line)
            if not m:
                continue
            k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
            if section == "delivery" and k == "to" and v:
                return v
            if section == "founder" and k == "email" and not to:
                to = v
    return to

APPLESCRIPT = r'''
on run argv
    set theTo to item 1 of argv
    set theFrom to item 2 of argv
    set theSubject to item 3 of argv
    set theBody to item 4 of argv
    tell application "Mail"
        set newMsg to make new outgoing message with properties {subject:theSubject, content:theBody, visible:false}
        tell newMsg
            make new to recipient at end of to recipients with properties {address:theTo}
            if theFrom is not "" then
                try
                    set sender of newMsg to theFrom
                end try
            end if
            if (count of argv) > 4 then
                repeat with i from 5 to (count of argv)
                    set p to item i of argv
                    try
                        make new attachment with properties {file name:(POSIX file p)} at after the last paragraph of content
                    end try
                end repeat
            end if
        end tell
        delay 2
        send newMsg
    end tell
    return "ok"
end run
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", default="")
    ap.add_argument("--from", dest="from_addr", default=os.environ.get("MAIL_FROM", ""))
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body")
    ap.add_argument("--attach", nargs="*", action="extend", default=[])
    args = ap.parse_args()

    allowed = founder_email()
    if not allowed:
        sys.exit("REFUSED: no founder email configured (config.yaml → founder.email, or MAIL_TO). "
                 "This tool only emails the founder, so set your own address first.")
    requested = (args.to or allowed).strip()
    if requested.lower() != allowed.strip().lower():
        sys.exit(f"REFUSED: may only email the founder ({allowed}); '{args.to}' is not allowed. "
                 f"This guardrail cannot be overridden.")
    to = allowed

    body = args.body if args.body is not None else (sys.stdin.read() if not sys.stdin.isatty() else "")
    attachments = []
    for f in args.attach:
        p = Path(f).resolve()
        if p.exists():
            attachments.append(str(p))
        else:
            print(f"WARN: attachment not found, skipping: {p}", file=sys.stderr)

    with tempfile.NamedTemporaryFile("w", suffix=".applescript", delete=False) as tf:
        tf.write(APPLESCRIPT)
        script_path = tf.name
    try:
        argv = ["osascript", script_path, to, args.from_addr, args.subject, body] + attachments
        res = subprocess.run(argv, capture_output=True, text=True)
    finally:
        os.unlink(script_path)

    if res.returncode != 0:
        sys.exit("ERROR sending via Mail.app: " + ((res.stderr or "").strip() or "unknown error") +
                 "\n(First run? Allow automation control of Mail in the macOS prompt / System Settings → "
                 "Privacy & Security → Automation, then retry.)")
    print(f"sent: '{args.subject}' -> {to}" + (f" ({len(attachments)} attachment(s))" if attachments else ""))

if __name__ == "__main__":
    main()
