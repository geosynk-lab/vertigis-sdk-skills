import { describe, expect, it } from "vitest";

import { auditCss, auditSource, createContext, finalize, RULES, runAudit, type RuleId, type Violation } from "./stylingAudit";

/**
 * Ratchet ceilings: current violation counts per rule. Counts may only go down.
 * On adoption, run the report and set each ceiling to the count found; after a cleanup, lower it.
 */
const BASELINE: Record<RuleId, number> = {
    "inline-static-style": 0,
    "mixed-class-and-style": 0,
    "inline-sx": 0,
    "typography-color-override": 0,
    "hardcoded-radius": 0,
    "inline-token-literal": 0,
    "token-fallback-drift": 0,
    "orphan-css-class": 0,
    "duplicate-css-class": 0,
    "css-important": 0,
    "css-root-scope": 0,
    "css-mui-override": 0,
    "css-font-family": 0,
    "css-hardcoded-radius": 0,
    "css-baseline": 0,
    "deep-mui-import": 0,
    "deprecated-input-props": 0,
    "theme-hardcoded-palette": 0,
    "file-too-large": 0,
};

/**
 * The only files allowed to break a rule once migration is complete; every other file must be fully compliant.
 * Give each entry a one-line reason, e.g.:
 *   // `display: none !important` hides a closed widget against host-shell inline display styles.
 *   "src/components/MyWidget/MyWidget.css": ["css-important"],
 *   // MUI derives hover/contrast colours from real palette values; CSS variables crash augmentColor().
 *   "src/tokens/VertiGisThemeProvider.tsx": ["theme-hardcoded-palette"],
 */
const KNOWN_EXCEPTIONS: Record<string, RuleId[]> = {};

/** Leave false while ceilings are above 0; set true once the codebase is migrated to lock every file. */
const ENFORCE_EXCEPTIONS_ONLY = false;

const format = (list: Violation[]) => list.map(v => `  ${v.file}:${v.line} [${v.rule}] ${v.detail}`).join("\n");

const auditTsx = (code: string, file = "src/components/Fixture.tsx") => {
    const ctx = createContext(new Map([["primaryForeground", "#212121"]]));
    auditSource(ctx, file, code);
    return finalize(ctx).map(v => v.rule);
};

const auditStyles = (css: string, tsx = "") => {
    const ctx = createContext(new Map([["primaryBorder", "#e0e0e0"]]));
    auditCss(ctx, "src/components/Fixture.css", css);
    if (tsx) auditSource(ctx, "src/components/Fixture.tsx", tsx);
    return finalize(ctx).map(v => v.rule);
};

describe("stylingAudit rule detectors", () => {
    it("flags static inline style but allows runtime-computed values", () => {
        expect(auditTsx(`<div style={{ display: "flex", gap: 8 }} />`)).toEqual(["inline-static-style"]);
        expect(auditTsx(`<div style={{ width: \`\${pct}%\`, left: x }} />`)).toEqual([]);
        expect(auditTsx(`<div style={{ background: UI_TOKENS.surface.primary }} />`)).toEqual(["inline-static-style"]);
    });

    it("flags elements styled by both className and static style", () => {
        expect(auditTsx(`<div className="A" style={{ padding: 4 }} />`)).toEqual(["inline-static-style", "mixed-class-and-style"]);
        expect(auditTsx(`<div className="A" style={{ height: h }} />`)).toEqual([]);
    });

    it("flags inline sx objects but allows style dictionaries", () => {
        expect(auditTsx(`<Box sx={{ p: 1 }} />`)).toEqual(["inline-sx"]);
        expect(auditTsx(`<Box sx={styles.root} />`)).toEqual([]);
    });

    it("flags Typography color overrides", () => {
        expect(auditTsx(`<Typography sx={{ color: "text.secondary" }} />`)).toEqual(["inline-sx", "typography-color-override"]);
        expect(auditTsx(`<Typography color="text.secondary" />`)).toEqual([]);
    });

    it("flags numeric borderRadius but allows tokens", () => {
        expect(auditTsx(`const s = { borderRadius: 4 };`)).toEqual(["hardcoded-radius"]);
        expect(auditTsx(`const s = { borderRadius: UI_TOKENS.shape.borderRadius, other: 0 };`)).toEqual([]);
    });

    it("flags raw token literals and fallback drift outside src/tokens", () => {
        expect(auditTsx(`const c = "var(--primaryForeground, #212121)";`)).toEqual(["inline-token-literal"]);
        expect(auditTsx(`const c = "var(--primaryForeground, #1e1e1e)";`)).toEqual(["inline-token-literal", "token-fallback-drift"]);
        expect(auditTsx(`const c = "var(--primaryForeground, #212121)";`, "src/tokens/ui.ts")).toEqual([]);
    });

    it("flags MUI hygiene issues", () => {
        expect(auditTsx(`import Box from "@mui/material/Box";`)).toEqual(["deep-mui-import"]);
        expect(auditTsx(`import { createTheme } from "@mui/material/styles";`)).toEqual([]);
        expect(auditTsx(`<TextField inputProps={{ maxLength: 3 }} />`)).toEqual(["deprecated-input-props"]);
        expect(auditTsx(`<CssBaseline />`)).toEqual(["css-baseline"]);
        expect(auditTsx(`createTheme({ palette: { text: { primary: "#212121" } } })`)).toEqual(["theme-hardcoded-palette"]);
        expect(auditTsx(`createTheme({ components: { MuiTypography: { styleOverrides: { root: { color: "inherit" } } } } })`)).toEqual([
            "theme-hardcoded-palette",
        ]);
    });

    it("flags oversized source files", () => {
        expect(auditTsx(Array(251).fill("const a = 1;").join("\n"))).toEqual(["file-too-large"]);
    });

    it("flags CSS hygiene issues", () => {
        expect(auditStyles(`:root { --x: 1px; }`)).toEqual(["css-root-scope"]);
        expect(auditStyles(`.A .MuiRadio-root { color: red !important; }`, `"A"`)).toEqual(["css-mui-override", "css-important"]);
        expect(auditStyles(`.A { font-family: var(--defaultFont); }`, `"A"`)).toEqual(["css-font-family"]);
        expect(auditStyles(`.A { font-family: var(--codeFont, monospace); }`, `"A"`)).toEqual([]);
        expect(auditStyles(`.A { border-radius: 4px; }`, `"A"`)).toEqual(["css-hardcoded-radius"]);
        expect(auditStyles(`.A { border-radius: var(--borderRadius, 4px); }`, `"A"`)).toEqual([]);
        expect(auditStyles(`.A { border: 1px solid var(--primaryBorder, #cbd5e1); }`, `"A"`)).toEqual(["token-fallback-drift"]);
    });

    it("flags orphan and duplicate CSS classes", () => {
        expect(auditStyles(`.A { gap: 1px; } .B { gap: 1px; }`, `<div className="A" />`)).toEqual(["orphan-css-class"]);
        // eslint-disable-next-line no-template-curly-in-string
        const dynamicClass = "className={`A-btn${on ? \" is-active\" : \"\"}`}";
        expect(auditStyles(`.A-btn.is-active { gap: 1px; }`, dynamicClass)).toEqual([]);
        const ctx = createContext();
        auditCss(ctx, "src/a.css", `.Shared { gap: 1px; }`);
        auditCss(ctx, "src/b.css", `.Shared { gap: 2px; }`);
        auditSource(ctx, "src/a.tsx", `<div className="Shared" />`);
        expect(finalize(ctx).map(v => v.rule)).toEqual(["duplicate-css-class", "duplicate-css-class"]);
    });
});

describe("styling hygiene of the codebase", () => {
    const violations = runAudit();

    it.each(Object.keys(RULES) as RuleId[])("%s does not exceed its baseline", rule => {
        const found = violations.filter(v => v.rule === rule);
        const message = `${RULES[rule]}\n${found.length} found, baseline ${BASELINE[rule]}:\n${format(found.slice(0, 40))}`;
        expect(found.length, message).toBeLessThanOrEqual(BASELINE[rule]);
    });

    it.runIf(ENFORCE_EXCEPTIONS_ONLY)("has no violations outside the known exceptions", () => {
        const found = violations.filter(v => !KNOWN_EXCEPTIONS[v.file]?.includes(v.rule));
        expect(found, `\n${format(found)}`).toEqual([]);
    });

    it.runIf(Boolean(process.env.STYLE_AUDIT_REPORT))("prints a report (STYLE_AUDIT_REPORT=1 [STYLE_AUDIT_FILE=path])", () => {
        const target = process.env.STYLE_AUDIT_FILE;
        const scoped = target ? violations.filter(v => v.file.includes(target)) : violations;
        const counts = Object.fromEntries((Object.keys(RULES) as RuleId[]).map(r => [r, scoped.filter(v => v.rule === r).length]));
        process.stdout.write(`${JSON.stringify(counts, null, 2)}\n${target ? `${format(scoped)}\n` : ""}`);
    });
});
