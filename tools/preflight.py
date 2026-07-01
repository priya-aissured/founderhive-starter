#!/usr/bin/env python3
"""Preflight check — is FounderHive set up enough to run agents?

Verifies config.yaml is filled (not placeholders), the source_folder exists, and the key context files
have been filled in (not left as templates). Run:  python3 tools/preflight.py
Exit code 0 = ready, 1 = issues found. Agents/onboarding can run this before doing real work.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDERS = ["Your Name", "you@yourcompany.com", "/absolute/path/to/your/company/folder",
                "Company One", "TEMPLATE (fill this in", "TEMPLATE (map your source folder"]

def cfg_value(key_path):
    """Fetch a nested key like founder.email or source_folder from config.yaml (minimal parser)."""
    f = ROOT / "config.yaml"
    if not f.exists():
        return None
    top, _, sub = key_path.partition(".")
    section = None
    for line in f.read_text().splitlines():
        if re.match(r"^\S", line):
            section = line.split(":", 1)[0].strip()
        m = re.match(r"^\s*([a-z_]+):\s*(.+?)\s*$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
        if sub and section == top and k == sub:
            return v
        if not sub and re.match(r"^\S", line) and k == top:
            return v
    return None

def main():
    problems, warnings = [], []

    if not (ROOT / "config.yaml").exists():
        problems.append("config.yaml is missing.")
    else:
        for kp in ["founder.name", "founder.email", "source_folder"]:
            v = cfg_value(kp)
            if not v or v in PLACEHOLDERS:
                problems.append(f"config.yaml → {kp} is still a placeholder / empty.")
        sf = cfg_value("source_folder")
        if sf and sf not in PLACEHOLDERS and not Path(sf).expanduser().exists():
            problems.append(f"source_folder path does not exist: {sf}")

    key_context = ["company-context/founder-bio.md", "company-context/founder-voice.md",
                   "company-context/company-overview.md", "company-context/knowledge-base.md"]
    for rel in key_context:
        p = ROOT / rel
        if not p.exists():
            problems.append(f"missing: {rel}")
            continue
        text = p.read_text()
        if any(ph in text for ph in ["TEMPLATE (fill this in", "TEMPLATE (map your source folder"]):
            warnings.append(f"{rel} still looks like an unfilled template.")

    print("FounderHive preflight\n" + "=" * 21)
    if problems:
        print("\nBLOCKERS (fix before running agents):")
        for p in problems: print("  ✗ " + p)
    if warnings:
        print("\nWARNINGS (agents will work but output will be weak until filled):")
        for w in warnings: print("  ! " + w)
    if not problems and not warnings:
        print("\n✓ Ready — config filled, source folder found, context files populated. Run an agent!")
    elif not problems:
        print("\n✓ Runnable, but fill the warnings for good output. Tip: run the 'setup' agent.")
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
