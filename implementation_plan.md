# Implementation plan: make the validator a trustworthy gate

> **Status: done** (#15, #16, #17). What landed on `main` and why differs in places from this plan; see [walkthrough.md](walkthrough.md).

## Problem

`validate_web_sdk.py` exits 1 on `vsw-ui`, the shared UI library that is meant to be the reference
(97 critical, 171 major, 31 minor). Almost all of it is noise, so a real new violation is invisible:

| Rule | Count | Where | Why it is noise |
|---|---|---|---|
| `HARDCODED_COLOR` + `TOKEN_REALIAS` | 96 | `UiShowcase.css` 39, `charts/palette.ts` 33, `color/ColorField.tsx` 12, showcase demos 12 | Token sources, colour-picker presets and the dev harness that simulates the host theme. Literals belong there. |
| `COMPONENT_CSS_PAIR` | 83 | every `.tsx` | vsw-ui keeps a component's look in `*.theme.ts` (as its AGENTS.md requires). The rule only accepts `<Name>.css`. |
| `MISSING_A11Y` (IconButton) | 53 | every `<IconButton label=…>` | The rule only knows MUI's `aria-label`; vsw-ui's `label` prop *is* the accessible name. |
| `HARDCODED_SPACING`, `REDUNDANT_INHERITED_TOKEN` | 28 | `UiShowcase.css` | Dev harness, not shipped. |

Second problem: the validator exists in two diverged copies.

- `~/.agents/skills/vertigis-{web,workflow}-sdk-skill` (what runs) is a superset: it adds `COMPONENT_CSS_PAIR`,
  `INLINE_SX*`, `TYPOGRAPHY_*`, `SX_COLOR_ON_CONTROL`, their fixtures, `install_styling_audit.py`, `styling-audit/`.
- This repo only adds two rule ids (`DISABLED_TOOLTIP_WRAPPER`, `UNSCOPED_THEME_OVERRIDE`) that are listed in
  `RULE_IDS` but have no catalogue entry, no check and no fixture: dead names.
- Within each copy the engine is byte-identical between the web and workflow skills; across copies it is not.

Decision (user, 2026-11-28): merge into this repo and make `~/.agents/skills` point here.

## Goal

1. `validate_web_sdk.py --path <vsw-ui>` exits 0, and every remaining finding is a real one.
2. A new violation fails the gate even in a repo with known debt (ratchet, not all-or-nothing).
3. One source for the validator; the web and workflow skills keep identical engine files.

## Steps

0. **Sync.** Copy the installed web and workflow skills into this repo (excluding `.venv`, `__pycache__`).
   Drop the two dead rule ids. Run both self-tests. Commit: `chore: sync installed validator into repo`.
1. **Per-project config, `.vertigis-rules.json`** at the `--path` root, read by `engine.py`:
   ```json
   {
     "wrapperLibraries": ["@geosynk/vsw-ui"],
     "overrides": [
       { "files": ["src/showcase/**"], "off": ["HARDCODED_COLOR", "TOKEN_REALIAS", "HARDCODED_SPACING"],
         "reason": "dev harness that simulates the host theme; never shipped" }
     ]
   }
   ```
   - `overrides` works like ESLint overrides: glob + rules turned off + a mandatory `reason`. A missing reason is
     an `INVALID_SUPPRESSION` finding. The report prints every override and how many findings it hid, so an
     exemption is visible, never silent.
   - Token sources: extend `in_tokens_dir` so `*.theme.ts` files are treated like `tokens/` (definitions, not use).
     Other token files (`charts/palette.ts`) are named in `overrides`, not guessed.
2. **`MISSING_A11Y`.** Resolve where `IconButton` / `TextField` is imported from in the file. From `@mui/material`:
   require `aria-label` (unchanged). From a `wrapperLibraries` package or a relative import: accept `label` or
   `aria-label`. Fixture: good (wrapper with `label`), bad (MUI without `aria-label`), bad (wrapper with neither).
3. **`COMPONENT_CSS_PAIR`.** Satisfied by `<Name>.css` **or** `<Name>.theme.ts` **or** a `*.theme.ts` in the same
   folder. Fixture for each. Update `rules.json` remediation text.
4. **Baseline ratchet.** `--update-baseline` writes `.vertigis-baseline.json`; a normal run reads it. A finding
   is fingerprinted by rule + file + normalised snippet (no line number, so edits above it do not break it).
   Baselined findings are reported as debt but do not fail; new findings fail. A baseline entry that no longer
   matches is reported as fixed so the file only shrinks. `verify_gate.py` honours it. Tests for: new finding
   fails, baselined passes, moved line still matches, fixed entry reported.
5. **Docs.** SKILL.md (Rule Validator section), `initiate_agents_md.py` template and the 6-tier gate text: describe
   `.vertigis-rules.json`, overrides need a reason, and the baseline.
6. **Mirror** engine/check/selftest files into the workflow skill (identical copies). Run both self-tests and
   `scripts/tests/test_examples.py`.
7. **vsw-ui** (separate repo, separate commit): add `.vertigis-rules.json` (showcase, `charts/palette.ts`,
   ColorField presets with reasons), run the validator, write a baseline for any real debt that remains
   (expected: `FILE_LENGTH_TARGET`, a few `RAW_HTML_TEXT`), confirm exit 0. Then add one deliberate violation
   and confirm exit 1, then remove it.
8. **Single source.** Move `~/.agents/skills/vertigis-{web,workflow}-sdk-skill` to
   `~/.agents/skills/.backup-2026-11-28/` (not deleted), symlink both to this repo, move `.venv` across or
   recreate it, and re-run step 7 through the symlink. `~/.claude/skills` already symlinks to `~/.agents`, so it
   follows.

## Tracking and verification

- GitHub issue in `geosynk-lab/vertigis-sdk-skills` with this plan; a results comment at the end.
- One commit per step in this repo, one in vsw-ui. Nothing is pushed without approval.
- Evidence (self-test, test output, validator before/after counts and exit codes) goes in `walkthrough.md`.

## Not in scope

- The ESLint import gate and visual regression tests (next items from the critique).
- Fixing vsw-ui's real debt; this only records it in the baseline.
- The `~/.agents` repo commit for the symlink swap: proposed after step 8 for your OK.

## Risks

- Overrides can become a loophole. Mitigation: mandatory reason, printed in every report with its hidden count.
- A baseline can hide new debt in the same file and snippet. Mitigation: the fingerprint includes the snippet,
  so only an identical finding is matched.
