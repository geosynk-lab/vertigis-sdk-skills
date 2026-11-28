"""Per-project settings (.vertigis-rules.json) and the findings baseline (.vertigis-baseline.json).

Identical copy in both VertiGIS SDK skills.

.vertigis-rules.json
    {
      "wrapperLibraries": ["@acme/ui"],
      "overrides": [{"files": ["src/showcase/**"], "off": ["HARDCODED_COLOR"], "reason": "dev harness"}]
    }
    An override turns rules off for files matching its globs. Its reason is mandatory and every report lists
    each override with the number of findings it hid, so no exemption is silent.

.vertigis-baseline.json
    Known findings, keyed by rule + file + the trimmed source line (no line number, so edits above a finding
    do not break the match). Baselined findings are reported as debt and do not fail the run; new ones do.
"""
from __future__ import annotations

import json
from collections import Counter
from fnmatch import fnmatchcase
from pathlib import Path

CONFIG_NAME = ".vertigis-rules.json"
BASELINE_NAME = ".vertigis-baseline.json"


def load_config(root: Path, catalog: dict) -> tuple[dict, list[str]]:
    """Return (config, problems). A problem becomes an INVALID_SUPPRESSION finding on the config file."""
    path = Path(root) / CONFIG_NAME
    if not Path(root).is_dir() or not path.is_file():
        return {"wrapperLibraries": [], "overrides": []}, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as err:
        return {"wrapperLibraries": [], "overrides": []}, [f"{CONFIG_NAME} is not valid JSON: {err}"]
    problems, overrides = [], []
    for i, entry in enumerate(data.get("overrides", [])):
        files, off, reason = entry.get("files") or [], entry.get("off") or [], str(entry.get("reason", "")).strip()
        unknown = [r for r in off if r not in catalog or r == "INVALID_SUPPRESSION"]
        if not files or not off or not reason or unknown:
            problems.append(f"overrides[{i}] needs files, off (known rule ids) and a reason"
                            + (f"; unknown: {', '.join(unknown)}" if unknown else ""))
            continue
        overrides.append({"files": list(files), "off": set(off), "reason": reason, "hidden": 0})
    return {"wrapperLibraries": list(data.get("wrapperLibraries", [])), "overrides": overrides}, problems


def apply_overrides(violations: list, overrides: list) -> list:
    kept = []
    for v in violations:
        hit = next((o for o in overrides
                    if v.rule in o["off"] and any(fnmatchcase(v.file, g) for g in o["files"])), None)
        if hit:
            hit["hidden"] += 1
        else:
            kept.append(v)
    return kept


def fingerprint(v, sources: dict) -> tuple[str, str, str]:
    src = sources.get(v.file)
    lines = src.raw.splitlines() if src else []
    text = lines[v.line - 1].strip() if 0 < v.line <= len(lines) else v.detail
    return v.rule, v.file, text


def apply_baseline(violations: list, sources: dict, path: Path) -> tuple[list, list, list]:
    """Split violations into (new, baselined); also return baseline entries that no longer match (fixed)."""
    entries = json.loads(path.read_text(encoding="utf-8")).get("entries", [])
    budget = Counter({(e["rule"], e["file"], e["snippet"]): e.get("count", 1) for e in entries})
    new, known = [], []
    for v in violations:
        key = fingerprint(v, sources)
        if budget[key] > 0:
            budget[key] -= 1
            known.append(v)
        else:
            new.append(v)
    fixed = [{"rule": r, "file": f, "snippet": s, "count": n} for (r, f, s), n in budget.items() if n > 0]
    return new, known, fixed


def write_baseline(violations: list, sources: dict, path: Path) -> int:
    counts = Counter(fingerprint(v, sources) for v in violations)
    entries = [{"rule": r, "file": f, "snippet": s, "count": n} for (r, f, s), n in sorted(counts.items())]
    path.write_text(json.dumps({"version": 1, "entries": entries}, indent=2) + "\n", encoding="utf-8")
    return len(violations)


def finish(violations: list, config: dict, sources: dict, baseline: Path | None, update: bool,
           always_new: set) -> tuple[list, list, list]:
    """Apply overrides, then the baseline. Rules in always_new (INVALID_SUPPRESSION) are never baselined."""
    kept = apply_overrides(violations, config["overrides"])
    if baseline is None:
        return kept, [], []
    if update:
        write_baseline([v for v in kept if v.rule not in always_new], sources, baseline)
    if not baseline.is_file():
        return kept, [], []
    new, known, fixed = apply_baseline(kept, sources, baseline)
    new += [v for v in known if v.rule in always_new]
    return new, [v for v in known if v.rule not in always_new], fixed
