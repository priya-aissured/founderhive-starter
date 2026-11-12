#!/usr/bin/env python3
# FounderHive · created by Priya Lakshmi (AISSURED) · https://github.com/priya-aissured/founderhive-starter · MIT
"""Load an example company so you can try FounderHive instantly — safely and reversibly.

  python3 tools/demo.py [name]     # default 'brightbook' — load the example (your files are backed up first)
  python3 tools/demo.py --restore  # put your own config + context back

It swaps config.yaml + company-context/ + gtm/ + content/ for the example's, backing up yours to
examples/.active-backup/ first. Nothing else is touched; delivery stays 'save' so no email is ever sent.
"""
import argparse, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BK = ROOT / "examples" / ".active-backup"
TARGETS = ["config.yaml", "company-context", "gtm", "content"]

def _copy(src, dst):
    if src.is_dir():
        for f in src.rglob("*"):
            if f.is_file():
                out = dst / f.relative_to(src); out.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, out)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)

def load(name):
    ex = ROOT / "examples" / name
    if not ex.is_dir():
        sys.exit(f"No example '{name}'. Available: " + ", ".join(p.name for p in (ROOT/'examples').iterdir() if p.is_dir() and not p.name.startswith('.')))
    if BK.exists():
        sys.exit("A demo is already loaded. Run `python3 tools/demo.py --restore` first.")
    BK.mkdir(parents=True)
    for t in TARGETS:                      # back up your own
        src = ROOT / t
        if src.exists(): _copy(src, BK / t)
    for t in TARGETS:                      # lay the example over the top
        exsrc = ex / t
        if exsrc.exists(): _copy(exsrc, ROOT / t)
    print(f"Loaded the '{name}' example. Your own files are backed up in examples/.active-backup/.\n"
          "Try:  /max challenge my pricing   ·   /dawn draft a blog   ·   /simon draft a one-pager\n"
          "Restore with:  python3 tools/demo.py --restore")

def restore():
    if not BK.exists():
        sys.exit("No demo is loaded (nothing to restore).")
    for t in TARGETS:
        cur = ROOT / t
        if cur.exists():
            shutil.rmtree(cur) if cur.is_dir() else cur.unlink()
        bak = BK / t
        if bak.exists(): _copy(bak, cur)
    shutil.rmtree(BK)
    print("Restored your own config + context. The example is unloaded.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", default="brightbook")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()
    restore() if args.restore else load(args.name)

if __name__ == "__main__":
    main()
