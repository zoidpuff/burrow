#!/usr/bin/env python
"""Privacy / confidentiality scan of the release tree.

Greps every file (plain text, the decompressed content of .gz files, and the text cells of .parquet
files when pyarrow is installed) for content that must not be published: absolute paths of a local
compute environment, agent temp/session paths and identifiers, e-mail addresses, IP addresses,
proxy settings, API keys / tokens. Legitimate hits are listed in ALLOW (file regex, line regex).

Project-specific patterns (user names, group / institution / host names, ...) are deliberately NOT
part of this file. Put them in an untracked local file (default ``.release_patterns.local`` in the
repository root, git-ignored; or the file named by ``$RELEASE_PATTERNS_FILE``), one rule per line:

    deny  <regex>                          # extra forbidden pattern (case-insensitive)
    allow <file-regex> <TAB> <line-regex>  # extra allowed context for any pattern
    # comment

  python scripts/check_release_clean.py [ROOT] [--patterns FILE] [--verbose]
"""
from __future__ import annotations

import argparse
import gzip
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", ".pytest_cache", "build", "dist", "outputs", "data"}
SKIP_FILES = {".release_patterns.local"}
BINARY_EXT = {".png", ".jpg", ".pdf", ".npz", ".pt", ".so", ".pyc", ".whl"}

PATTERNS = {
    "abs_path": r"(?<![\w.<])/(?:cluster|scratch|home|Users|workspace|mnt|nfs|net|project|work|gpfs|lustre|srv)/[\w.-]",
    "tmp_agent_path": r"/tmp/claude|/tmp/[\w-]*\d{4,}",
    "windows_path": r"\b[A-Z]:\\\\(?:Users|home)\\\\",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}",
    "ip_address": r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])",
    "proxy": r"proxy",
    "token": r"token|api[_-]?key|secret|password|bearer\s",
    "key_shape": r"\bsk-[A-Za-z0-9_-]{8,}|\bghp_[A-Za-z0-9]{20,}|\bxox[bp]-|\bAKIA[0-9A-Z]{16}\b(?=.*(aws|key))",
    "session_id": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|claude-\d{3,}",
    "pid": r"\bPIDs?\s*[:=]?\s*\d{3,}|\bpid\s*[:=]\s*\d+",
}

# (file regex, line regex, reason) -- a hit is allowed if both match (line regex searched in +-80 chars)
ALLOW = [
    (r".*", r"(?i)^(?!.*(https?_proxy|no_proxy|proxy\s*[=:]\s*\S*(://|\d+\.\d+|:\d{2,})|--proxy|proxy\.\w|://)).*\bprox(y|ies)\b",
     "scientific use of the word 'proxy' (no proxy setting / URL on the line)"),
    (r".*", r"(?i)^(?!.*(token\s*[=:]\s*['\"]?[A-Za-z0-9_-]{12,}|bearer|api[_-]?key|\b[A-Z]+_TOKEN\b|secret|password)).*\btokens?\b",
     "parsing tokens (e.g. residue identifiers), not credentials"),
    (r".*", r"noreply@anthropic\.com|burrow-authors@users\.noreply\.github\.com", "commit attribution placeholders"),
    (r"^examples/AF-.*\.cif\.gz$", r"^(ATOM|HETATM)|_ma_|_atom_site|_entity_poly", "coordinates / sequences of the AFDB example"),
    (r"^scripts/check_release_clean\.py$", r".*", "this file defines the patterns"),
]


def load_local(path: Path):
    """Extra deny / allow rules from an untracked local file (see module docstring)."""
    deny, allow = {}, []
    if not path or not path.exists():
        return deny, allow
    for i, line in enumerate(path.read_text().splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        kind, _, rest = s.partition(" ")
        if kind == "deny":
            deny[f"local{i}"] = rest.strip()
        elif kind == "allow":
            f, _, l = rest.strip().partition("\t")
            allow.append((f.strip(), l.strip(), f"local rule line {i}"))
        else:
            raise SystemExit(f"{path}:{i}: expected 'deny <regex>' or 'allow <file-regex><TAB><line-regex>'")
    return deny, allow


def iter_text(path: Path):
    """Yield (line_no, line) of the file's textual content."""
    suf = "".join(path.suffixes[-2:]).lower()
    if path.suffix.lower() in BINARY_EXT:
        return
    if path.suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError:
            print(f"[warn] pyarrow missing, parquet not scanned: {path}", file=sys.stderr)
            return
        t = pq.read_table(path)
        for i, row in enumerate(t.to_pylist(), 1):
            yield i, " ".join(str(v) for v in row.values())
        return
    try:
        raw = gzip.open(path, "rb").read() if suf.endswith(".gz") else path.read_bytes()
    except OSError as e:
        print(f"[warn] cannot read {path}: {e}", file=sys.stderr)
        return
    text = raw.decode("utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        yield i, line


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", type=Path, default=ROOT)
    ap.add_argument("--patterns", type=Path, default=None,
                    help="local rules file (default: $RELEASE_PATTERNS_FILE or <root>/.release_patterns.local)")
    ap.add_argument("--verbose", action="store_true", help="also list allowed hits")
    a = ap.parse_args(argv)
    lp = a.patterns or Path(os.environ.get("RELEASE_PATTERNS_FILE", a.root / ".release_patterns.local"))
    deny, extra_allow = load_local(lp)
    print(f"[check_release_clean] local rules: {lp if lp.exists() else 'none'} ({len(deny)} deny, {len(extra_allow)} allow)")
    pats = {k: re.compile(v, re.I if k != "session_id" else 0) for k, v in {**PATTERNS, **deny}.items()}
    allow = [(re.compile(f), re.compile(l), why) for f, l, why in ALLOW + extra_allow]
    bad, n_files, n_allowed = [], 0, 0
    for p in sorted(a.root.rglob("*")):
        if not p.is_file() or p.name in SKIP_FILES or any(part in SKIP_DIRS for part in p.relative_to(a.root).parts):
            continue
        rel = p.relative_to(a.root).as_posix()
        n_files += 1
        for name in (rel,):  # file names themselves
            for k, rx in pats.items():
                if k not in ("token", "proxy") and rx.search(name):
                    bad.append((rel, 0, k, name))
        for ln, line in iter_text(p):
            for k, rx in pats.items():
                for m in rx.finditer(line):
                    ctx = line[max(0, m.start() - 80): m.end() + 80]
                    if any(fr.search(rel) and lr.search(ctx) for fr, lr, _ in allow):
                        n_allowed += 1
                        if a.verbose:
                            print(f"allowed  {rel}:{ln} [{k}] {ctx.strip()[:160]}")
                        continue
                    bad.append((rel, ln, k, ctx.strip()[:200]))
    for rel, ln, k, ctx in bad:
        print(f"FORBIDDEN {rel}:{ln} [{k}] {ctx}")
    print(f"[check_release_clean] {n_files} files scanned, {len(bad)} forbidden hit(s), {n_allowed} allowed hit(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
