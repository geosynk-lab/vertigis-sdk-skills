# Walkthrough: validator as a trustworthy gate (#15)

Branch `fix/validator-gate-15` in this repo; branch `chore/validator-gate` in vsw-ui. Nothing pushed.

## What changed

| Commit | Change |
|---|---|
| `52a3c89` | Sync the installed (`~/.agents`) web and workflow skills into this repo; the installed copy was the newer superset. |
| `cd0464f` | `project.py`: `.vertigis-rules.json` overrides (mandatory reason, counted in every report) and `.vertigis-baseline.json` ratchet. `*.theme.ts` counts as a token definition file. CLI flags `--baseline`, `--update-baseline`, `--no-baseline`; `verify_gate.py` honours the baseline. |
| `3655040` | `MISSING_A11Y` resolves a control's import: MUI `IconButton` (also aliased) needs `aria-label`; a wrapper (relative import or `wrapperLibraries`) may use `label`. |
| `d51cdb5` | `COMPONENT_CSS_PAIR` accepts `<Name>.css` or a `*.theme.ts` in the same folder. |
| `373fdf0` | Docs (SKILL.md, AGENTS.md templates) in both skills; shared engine files mirrored into the workflow skill. |
| `05ca197` | Merge the forked rule sets; self-test green in both skills (see *Correction* below). |
| vsw-ui `ac8d765`, `130b881` | `.vertigis-rules.json` (3 overrides, each with a reason) and `.vertigis-baseline.json` (46, then 39 findings after the merge). |
| (not committed) | `~/.agents/skills/vertigis-{web,workflow}-sdk-skill` are now symlinks to this repo; the old folders are in `~/.agents/.install-backup/2026-11-28/`. |

## Evidence

vsw-ui, `validate_web_sdk.py --path .`

| State | Result | Exit |
|---|---|---|
| Before (installed validator) | critical=97 major=171 minor=31 | 1 |
| New rules, no config | critical=97 major=60 minor=31 (all 53 `MISSING_A11Y` false positives gone) | 1 |
| + overrides | critical=1 major=14 minor=31, overridden=142 | 1 |
| + baseline | critical=0 major=0 minor=0, baselined=46 | 0 |
| `--strict` | same | 0 |
| + deliberate `color: #ff0000` in `src/lib/components/tags/Probe.css` | critical=1 (the probe) | 1 |
| probe removed | | 0 |
| through `~/.agents` symlink | PASS | 0 |
| `verify_gate.py --path .` | APPROVED | 0 |

Tests

| Test | Web | Workflow |
|---|---|---|
| `tests/test_project.py` (6 cases: override hides and counts, missing reason invalid, unknown rule invalid, baseline pass/new fail, moved line + fixed report, duplicate count) | pass | pass |
| `tests/test_examples.py` | all examples pass | all examples pass |
| Fixtures `MISSING_A11Y` bad/good, `COMPONENT_CSS_PAIR` bad/good (run directly) | as expected | n/a |
| `--self-test` | **pass, 0 problems** | **pass, 0 problems** |

Self-test history: `main` 48 / 30 problems, installed copy 18 / 9, after `05ca197` 0 / 0. A negative probe (a
broken `UNGUARDED_DEV_AUTH` good fixture in a scratch copy) makes it exit 1, so the pass is real. Running
`python3 selftest.py` directly proves nothing (no entry point); the real command is `--self-test`.

After the merge, vsw-ui: normal and `--strict` exit 0, a deliberate `color: #ff0000` exits 1, `verify_gate.py`
APPROVED, `npm run verify:styles` PASS.

## Correction: the forks were not a superset

The first sync assumed the installed copy was a superset because no *file* existed only in the repo. That was
wrong: the repo's `main` had real checks inside shared files (from `f33f473`) that the installed copy lacked,
and the two copies held opposite styling policies. `05ca197` merges them:

- Restored: `DISABLED_TOOLTIP_WRAPPER`, `UNSCOPED_THEME_OVERRIDE`, `MARGIN_LEAKAGE`, `NON_MUI_CONTAINMENT`,
  `STANDARDIZED_SPACING`, `SPACING_TOKENS_DECLARED`, `TOKEN_EXACT_NAME`, `EMPTY_CSS_FILE`.
- Added (catalogued but never implemented anywhere): `UNGUARDED_DEV_AUTH`.
- Dropped, because they contradict MUI's guidance: `INLINE_SX`, `INLINE_SX_LAYOUT` (MUI: `sx` is the tool for
  one-off styles, layout included), `COMPONENT_CSS_PAIR` (CSS required) and `COMPONENT_CSS_FILE` (CSS forbidden);
  MUI neither requires nor forbids component CSS.
- `NO_COSMETIC_SX` stays an opt-in Tier 3 house rule (`verify_zero_cosmetic_sx.py`). In the shared validator it
  would contradict the skill's own token-pairing guidance, which puts token colour pairs in `sx`. Suppressions
  naming it are accepted (with a reason) so the Tier 3 tool can still read them.

## Known limits

- `verify_gate.py` prints "0 violations" without mentioning baselined debt.
- In `--file` mode the baseline is not applied (paths are relative to the file, not the project).
- The installed skill now follows whatever branch is checked out in this repo.

## Methodology

**Why the old gate guaranteed nothing.** A gate is a binary signal: pass means "no known problem". When the
reference project already fails with 268 findings, every run fails, so a new failure carries no information.
People and agents learn to ignore it. Trust needs two things: the gate passes on good code, and it fails on
any *new* bad code.

**False positives come from missing context, not from strict rules.** The rules were right in spirit but
blind to project shape:
- *Where the code lives.* A colour literal in a component is a bug; in a token file, a chart palette or a
  dev harness it is a definition or data. Overrides give the validator that context per path. Making the
  reason mandatory and printing every override with its hidden count keeps it honest: an exemption is a
  visible, reviewable decision, like an ESLint override, not a silent hole.
- *What a name refers to.* `<IconButton>` can be MUI's (needs `aria-label`) or a wrapper whose `label`
  prop becomes the accessible name. Reading the import tells them apart; judging by origin also closes the
  loophole of aliasing MUI's control to dodge the check.
- *How the project styles components.* A `*.theme.ts` with MUI `styleOverrides` is a legitimate home for a
  component's look, so it satisfies the pairing rule.

**The ratchet.** Real debt cannot always be fixed today, but it must not grow. The baseline stores each known
finding as rule + file + trimmed source line, without a line number, so edits elsewhere in the file do not
invalidate it, while a second identical finding still exceeds the stored count and fails. Entries that no
longer match are reported as fixed, so the file only shrinks. This is the same pattern as lint "baseline"
or "suppressions" files in large codebases: freeze the past, gate the future.

**One source of truth.** Two copies of the validator had drifted in both directions. Symlinking the installed
location to the repo means every client (Claude, Codex, Gemini) runs the code that is versioned and tested.

---

# Walkthrough: keeping the skill, the SDK and vsw-ui in sync (#16, vsw-ui #2)

Branches: `feat/vsw-ui-profile` here (`16108dd`, `0a204a5`), `feat/ui-contract` in vsw-ui (`05f98a6`, `2a4c1ca`). Not pushed.

## Evidence

| Check | Result |
|---|---|
| `check-contract.mjs` | PASS, 65 components; probe (rename one entry) FAIL with 2 problems, exit 1 |
| ESLint gate test | 9 bad imports blocked, 5 good imports allowed |
| Screenshot test | 28 images; repeat runs differ by 0-2 px; 4 px badge probe fails exactly 2 images (205 px); revert passes |
| Skill self-test | web 0, workflow 0 problems; `test_project.py` (incl. 2 profile tests) and `test_examples.py` pass in both |
| Setup script | vsw-ui project: 85-line AGENTS.md with the short UI section and the profile config; plain project: 100 lines, unchanged |
| End to end | sample app importing `@mui/x-data-grid`: ESLint exit 1, validator exit 1 (`UI_IMPORT`); after switching to vsw-ui both exit 0 |
| vsw-ui gate | `tsc`, lint, `verify:styles`, `check:contract`, validator, `build`, `build:lib`: all exit 0 |

## Methodology

**One owner per concern.** Drift happens when two places describe the same thing. The SDK is the platform, vsw-ui owns
everything visual, and the skill owns SDK know-how. Each fact now lives once: the component catalogue lives in vsw-ui
(`contract/components.json`, next to the code it describes), and everything else reads it.

**Ship the rules with the package.** Agents and tools read `node_modules/@geosynk/vsw-ui/...`, so the rules always match
the installed version, with no copy in the skill to update. This is the same idea as a library shipping its own
TypeScript types: the consumer gets the contract of exactly the version it installed.

**Block at the import.** "Use vsw-ui's DataGrid" is a choice made at one line, the import. ESLint
`no-restricted-imports` checks that line in the editor, in CI and for an agent, and its message names the replacement,
so the fix is in the error. The validator's `UI_IMPORT` reads the same contract, so the two cannot disagree.

**Verify once, where the thing is built.** Token pairing, contrast and theme rules check how a look is built. In an app
that cannot build a look (imports only from vsw-ui, no cosmetic code), those rules have nothing to find, so the profile
turns them off and says so in every report. Two small rules (`UI_IMPORT`, `APP_COSMETIC_CSS`) prove that the app
really cannot build a look, which is what makes turning the others off safe.

**Test the pixels, calibrate the threshold.** Code rules cannot see that a hover turned the wrong colour; screenshots
can. The threshold came from measurement: identical runs differ by 0-2 px, and a real 4 px change moves about 200 px,
so 10 px separates noise from change. The first version used a percentage and missed the change, which the probe exposed.
