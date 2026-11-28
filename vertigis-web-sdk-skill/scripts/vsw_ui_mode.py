"""vsw-ui mode for initiate_agents_md.py: a project that depends on @geosynk/vsw-ui gets its UI rules from the
installed package, so AGENTS.md carries a short pointer instead of the long styling sections."""
from __future__ import annotations

import json
import re
from pathlib import Path

PACKAGE = "@geosynk/vsw-ui"
CONFIG = ".vertigis-rules.json"

UI_SECTION = """## 1. UI Comes Only From `@geosynk/vsw-ui`
- **Read before writing UI**: `node_modules/@geosynk/vsw-ui/COMPONENTS.md` ("for X use Y" and the hard rules). It matches the installed version, so trust it over memory or older notes.
- **Import every control from vsw-ui**: `Button`, `IconButton`, `TextField`, `Select`, `Dialog`, `Tabs`, `DataGrid` (`@geosynk/vsw-ui/data-grid`), charts (`@geosynk/vsw-ui/charts`), icons (`<Icon name>`). From `@mui/material` import only layout and text (`Box`, `Stack`, `Grid`, `Typography`, `Tooltip`, `Divider`, `Paper`, `Card`).
- **Wrap the app once in `VsuiThemeProvider`**. Never create your own MUI theme or mount `<CssBaseline />`.
- **No look in app code**: no colours, borders, radii, shadows or font settings in `sx`, `style` or app CSS; app CSS lays things out only. Layout uses `Stack` / `Box` with the 8px grid (`SPACE`, `SPACE_ROLE`).
- **Missing component or variant**: do not build it from MUI in the app. Stop and ask, or add it to vsw-ui (`src/lib/`, a `*.theme.ts`, and the showcase).
- **Enforced by**: the `@geosynk/vsw-ui/eslint` preset (last in `eslint.config.js`) and the Rule Validator with `"profile": "vsw-ui"` in `.vertigis-rules.json` (`UI_IMPORT`, `APP_COSMETIC_CSS`). Token, theme and component-styling rules are checked once in vsw-ui itself, not in this app.
"""

HEADER_GENERIC = "semantic HTML with co-located namespaced CSS, two-tier theming architecture via VertiGisThemeProvider for MUI"
HEADER_VSW_UI = "UI only from @geosynk/vsw-ui inside VsuiThemeProvider"


def uses_vsw_ui(target: Path) -> bool:
    try:
        pkg = json.loads((target / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return any(PACKAGE in (pkg.get(k) or {}) for k in ("dependencies", "devDependencies", "peerDependencies"))


def tailor(body: str) -> str:
    """Swap sections 1-2 (typography, host styling) for UI_SECTION and renumber the sections after them."""
    start, end = body.index("## 1. "), body.index("## 3. ")
    body = body[:start] + UI_SECTION + "\n" + body[end:]
    body = re.sub(r"^## (\d+)\. ", lambda m: f"## {int(m.group(1)) - 1 if int(m.group(1)) > 2 else m.group(1)}. ",
                  body, flags=re.M)
    return body.replace(HEADER_GENERIC, HEADER_VSW_UI)


def configure_project(target: Path) -> list[str]:
    """Write the validator profile when no config exists; return notes for the user."""
    notes = []
    config = target / CONFIG
    if not config.exists():
        config.write_text(json.dumps({"profile": "vsw-ui"}, indent=2) + "\n", encoding="utf-8")
        notes.append(f"Created {config} with the vsw-ui validator profile.")
    elif '"profile"' not in config.read_text(encoding="utf-8"):
        notes.append(f'{config} exists without a profile; add "profile": "vsw-ui" to it.')
    eslint = next((p for p in target.glob("eslint.config.*")), None)
    if eslint is None or "@geosynk/vsw-ui/eslint" not in eslint.read_text(encoding="utf-8"):
        notes.append('Add the import gate last in eslint.config.js: import vswUi from "@geosynk/vsw-ui/eslint"; '
                     "export default [...sdkConfig, ...vswUi];")
    return notes
