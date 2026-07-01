#!/usr/bin/env python3
"""Send an email (with optional attachment) via the macOS Mail app — NO password stored.

Drives Apple Mail (already signed into your account) through AppleScript. FounderHive agents use this to
deliver drafts to you for approval. First run triggers a one-time macOS prompt: "<app> wants to control
Mail" → click OK. Requires Mail.app configured with an account that can send as the From address.

Recipient: pass --to, or set the MAIL_TO environment variable (put your address there, matching
config.yaml founder.email). There is no hardcoded recipient.

Usage:
  python3 tools/send_mail_macos.py --to you@co.com --subject "..." --body "..." [--attach f.docx ...]
"""
import argparse, subprocess, sys, tempfile, os
from pathlib import Path

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
    ap.add_argument("--to", default=os.environ.get("MAIL_TO", ""),
                    help="recipient (or set MAIL_TO env). Should match config.yaml founder.email.")
    ap.add_argument("--from", dest="from_addr", default=os.environ.get("MAIL_FROM", ""))
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body")
    ap.add_argument("--attach", nargs="*", default=[])
    args = ap.parse_args()

    if not args.to:
        sys.exit("ERROR: no recipient. Pass --to you@yourcompany.com or set MAIL_TO. (See config.yaml founder.email.)")

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
        argv = ["osascript", script_path, args.to, args.from_addr, args.subject, body] + attachments
        res = subprocess.run(argv, capture_output=True, text=True)
    finally:
        os.unlink(script_path)

    if res.returncode != 0:
        sys.exit("ERROR sending via Mail.app: " + ((res.stderr or "").strip() or "unknown error") +
                 "\n(First run? Allow automation control of Mail in the macOS prompt / System Settings → "
                 "Privacy & Security → Automation, then retry.)")
    print(f"sent: '{args.subject}' -> {args.to}" + (f" ({len(attachments)} attachment(s))" if attachments else ""))

if __name__ == "__main__":
    main()
