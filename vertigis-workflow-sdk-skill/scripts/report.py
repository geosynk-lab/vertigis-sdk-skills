"""Report rendering and exit policy. Identical copy in both VertiGIS SDK skills."""
from __future__ import annotations

import json

from engine import SEVERITIES, severity_of

WEIGHTS = {"critical": 10, "major": 3, "minor": 1}
COLORS = {"critical": "\033[31;1m", "major": "\033[33;1m", "minor": "\033[36m"}
RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"


def counts(result: dict) -> dict:
    out = {s: 0 for s in SEVERITIES}
    for v in result["violations"]:
        out[severity_of(result["catalog"][v.rule], result["sdk"])] += 1
    return out


def score(result: dict) -> int:
    """Informational only; never decides pass/fail."""
    return max(0, 100 - sum(WEIGHTS[s] * n for s, n in counts(result).items()))


def exit_code(result: dict, strict: bool) -> int:
    c = counts(result)
    return 1 if c["critical"] or (strict and c["major"]) else 0


def _rows(result: dict):
    for v in result["violations"]:
        entry = result["catalog"][v.rule]
        yield v, entry, severity_of(entry, result["sdk"])


def render_ansi(result: dict, strict: bool) -> str:
    lines = []
    for v, entry, sev in _rows(result):
        lines.append(f"{BOLD}{v.file}:{v.line}{RESET}  {COLORS[sev]}{v.rule}  {sev}{RESET}  {entry['summary']}")
        if v.detail:
            lines.append(f"    {DIM}{v.detail}{RESET}")
        lines.append(f"    fix: {entry['remediation']}  {DIM}[{entry['skill_ref']}]{RESET}")
    for s in result["suppressions"]:
        lines.append(f"{DIM}suppressed {s.rule} at {s.file}:{s.line} ({s.scope}) -- {s.reason}{RESET}")
    c = counts(result)
    verdict = "FAIL" if exit_code(result, strict) else "PASS"
    lines.append(f"{BOLD}{verdict}{RESET}  {result['files']} files  critical={c['critical']} major={c['major']} "
                 f"minor={c['minor']}  suppressed={len(result['suppressions'])}  score={score(result)} (informational)")
    return "\n".join(lines)


def render_json(result: dict, strict: bool) -> str:
    return json.dumps({
        "sdk": result["sdk"],
        "files": result["files"],
        "passed": exit_code(result, strict) == 0,
        "counts": counts(result),
        "score": score(result),
        "violations": [{"rule": v.rule, "severity": sev, "file": v.file, "line": v.line, "detail": v.detail,
                        "summary": e["summary"], "remediation": e["remediation"], "skill_ref": e["skill_ref"]}
                       for v, e, sev in _rows(result)],
        "suppressions": [s.__dict__ for s in result["suppressions"]],
    }, indent=2)


def render_markdown(result: dict, strict: bool) -> str:
    c = counts(result)
    verdict = "FAIL" if exit_code(result, strict) else "PASS"
    out = [f"# VertiGIS {result['sdk']} SDK rule report: {verdict}", "",
           f"Files: {result['files']} | critical: {c['critical']} | major: {c['major']} | minor: {c['minor']} | "
           f"suppressed: {len(result['suppressions'])} | score: {score(result)} (informational)", "",
           "| Severity | Rule | Location | Detail | Fix |", "|---|---|---|---|---|"]
    esc = lambda t: str(t).replace("|", "\\|").replace("\n", " ")
    for v, e, sev in _rows(result):
        out.append(f"| {sev} | `{v.rule}` | `{v.file}:{v.line}` | {esc(v.detail)} | {esc(e['remediation'])} |")
    if result["suppressions"]:
        out += ["", "## Suppressions", "", "| Rule | Location | Scope | Reason |", "|---|---|---|---|"]
        out += [f"| `{s.rule}` | `{s.file}:{s.line}` | {s.scope} | {esc(s.reason)} |" for s in result["suppressions"]]
    return "\n".join(out) + "\n"


RENDERERS = {"ansi": render_ansi, "json": render_json, "markdown": render_markdown}
