#!/usr/bin/env python3
# FounderHive · created by Priya Lakshmi (AISSURED) · https://github.com/priya-aissured/founderhive-starter · MIT
"""Non-destructive file organiser / cataloguer for FounderHive.

Scans a founder's root directory (READ-ONLY) and builds a categorised inventory, so FounderHive's agents
know where everything lives. It buckets files into: Product, Marketing, Investor, Expenses, Code,
Customers, Legal/Admin, Research, Other.

SAFETY: it NEVER moves, renames, edits or deletes your files. It reads filenames + metadata only (not file
contents) and writes a single index INTO the FounderHive project: company-context/file-inventory.csv.
To physically reorganise, it can emit a *proposed move plan* you review and run yourself — nothing is ever
moved for you.

Usage:
  python3 tools/organise.py [--root /path/to/your/company/folder] [--max 8000]
  python3 tools/organise.py --plan        # also writes a proposed-structure move plan (NOT executed)
"""
import argparse, csv, os, re, sys, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_PROJ = HERE.parent

# --- directories/files we never descend into or list (noise / code internals / secrets) ---
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", "dist", "build", ".next",
             ".cache", ".idea", ".vscode", ".pytest_cache", ".mypy_cache", "target", ".terraform",
             "vendor", ".gradle", ".tox", "coverage", ".parcel-cache", "Pods", ".svn"}
SKIP_FILES = {".DS_Store", "Thumbs.db", ".env", ".env.local"}
CODE_MARKERS = {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
                "pom.xml", "build.gradle", ".git", "Gemfile", "composer.json", "Dockerfile"}
CODE_EXT = {".py",".js",".ts",".tsx",".jsx",".java",".go",".rb",".rs",".cpp",".c",".h",".cs",".php",
            ".sql",".sh",".swift",".kt",".scala",".vue",".html",".css",".yaml",".yml",".toml"}

# keyword → category (checked in order; first hit wins). Keywords matched in the lowercased path.
RULES = [
    ("Investor",    ["investor","fundrais","pitch","deck","cap table","captable","seis","eis","term sheet",
                     "termsheet","safe note","valuation","data room","dataroom","one-pager","onepager","raise"]),
    ("Expenses",    ["expense","invoice","receipt","finance","forecast","budget","payroll","tax","vat",
                     "bank statement","bookkeep","p&l","profit","ledger","accounting"]),
    ("Customers",   ["customer","client","crm","pilot","design partner","prospect","sow","support",
                     "onboarding","meeting note","meeting-prep","account plan"]),
    ("Legal/Admin", ["legal","contract","nda","msa","dpa","\\bip\\b","gdpr","incorpor","articles",
                     "shareholder","compliance","insurance","policy","agreement","equity"]),
    ("Marketing",   ["market","brand","content","blog","linkedin","social","campaign","\\bseo\\b","logo",
                     "press","newsletter","website","webinar","event","copy"]),
    ("Research",    ["research","competitor","whitepaper","white paper","study","survey","analysis","report"]),
    ("Product",     ["product","\\bprd\\b","roadmap","spec","requirement","design","feature","wireframe",
                     "architecture","backlog","user story","mockup","prototype"]),
]
EXT_FALLBACK = {".xlsx":"Expenses",".xls":"Expenses",".csv":"Expenses",
                ".fig":"Product",".sketch":"Product",
                ".pptx":"Marketing",".key":"Marketing",
                ".md":"Product",".doc":"Other",".docx":"Other",".pdf":"Other"}

def read_source_folder():
    f = ROOT_PROJ / "config.yaml"
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r"^\s*source_folder:\s*(.+?)\s*$", line)
            if m:
                return os.path.expanduser(m.group(1).strip().strip('"').strip("'"))
    return ""

def classify(rel_path, ext):
    low = rel_path.lower()
    if ext in CODE_EXT:
        return "Code"
    for cat, kws in RULES:
        for kw in kws:
            if (re.search(kw, low) if "\\" in kw else kw in low):
                return cat
    return EXT_FALLBACK.get(ext, "Other")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="")
    ap.add_argument("--max", type=int, default=8000)
    ap.add_argument("--plan", action="store_true", help="also write a proposed move plan (NOT executed)")
    args = ap.parse_args()

    root = args.root or read_source_folder()
    if not root:
        sys.exit("No root to scan. Pass --root /path/to/folder or set source_folder in config.yaml.")
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")
    if ROOT_PROJ == root or ROOT_PROJ in root.parents or root in ROOT_PROJ.parents:
        print(f"WARNING: scanning {root} which overlaps the FounderHive project — results may include the kit itself.", file=sys.stderr)

    rows, code_projects, n, truncated = [], [], 0, False
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # a code repo / build root → record once as a Code project, don't descend
        if any((d / m).exists() for m in CODE_MARKERS) and d != root:
            code_projects.append(str(d.relative_to(root)))
            dirnames[:] = []       # prune
            continue
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not x.startswith(".")]
        for fn in filenames:
            if fn in SKIP_FILES or fn.startswith("."):
                continue
            p = d / fn
            try:
                st = p.stat()
            except OSError:
                continue
            rel = str(p.relative_to(root))
            ext = p.suffix.lower()
            rows.append({"path": rel, "category": classify(rel, ext), "ext": ext,
                         "size_kb": round(st.st_size/1024, 1),
                         "modified": datetime.date.fromtimestamp(st.st_mtime).isoformat()})
            n += 1
            if n >= args.max:
                truncated = True; break
        if truncated:
            break

    # write inventory into the FounderHive project (never into the scanned root)
    out = ROOT_PROJ / "company-context" / "file-inventory.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path","category","ext","size_kb","modified"])
        w.writeheader(); w.writerows(sorted(rows, key=lambda r: (r["category"], r["path"])))

    # summary
    from collections import Counter
    cats = Counter(r["category"] for r in rows)
    print(f"Scanned (read-only): {root}")
    print(f"Catalogued {len(rows)} files" + (f" (capped at {args.max})" if truncated else "")
          + f"; {len(code_projects)} code project(s) detected.")
    for c in ["Product","Marketing","Investor","Expenses","Customers","Legal/Admin","Research","Code","Other"]:
        if cats.get(c): print(f"  {c:<12} {cats[c]}")
    if code_projects:
        print("  Code projects: " + ", ".join(code_projects[:8]) + (" …" if len(code_projects) > 8 else ""))
    print(f"\nInventory → {out.relative_to(ROOT_PROJ)}")
    print("Next: an agent (e.g. Honey) turns this into company-context/file-map.md and your knowledge base.")

    if args.plan:
        plan = ROOT_PROJ / "company-context" / "proposed-move-plan.sh"
        with plan.open("w") as fh:
            fh.write("#!/usr/bin/env bash\n# PROPOSED file organisation — REVIEW before running. FounderHive does NOT run this.\n")
            fh.write("# It COPIES (not moves) your files into an 'Organised/' folder so originals are untouched.\n")
            fh.write(f'ROOT="{root}"\nDEST="$ROOT/Organised"\n')
            for c in sorted(cats):
                fh.write(f'mkdir -p "$DEST/{c}"\n')
            for r in rows:
                fh.write(f'cp -n "$ROOT/{r["path"]}" "$DEST/{r["category"]}/" 2>/dev/null || true\n')
        print(f"Proposed move plan (copies only, NOT executed) → {plan.relative_to(ROOT_PROJ)} — review, then run it yourself.")

if __name__ == "__main__":
    main()
