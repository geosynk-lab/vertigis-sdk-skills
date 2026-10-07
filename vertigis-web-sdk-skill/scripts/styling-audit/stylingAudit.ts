/**
 * Static styling audit for the VertiGIS Web SDK styling rules.
 * Parses TS/TSX with the TypeScript compiler API and CSS with lightweight selector/declaration scanning.
 * Used only by stylingAudit.test.ts; never bundled.
 * Canonical token fallbacks are read from src/tokens/ui.ts when present.
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

import * as ts from "typescript";

export const RULES = {
    "inline-static-style": "style={{}} holds fixed values; move them to the co-located CSS file",
    "mixed-class-and-style": "element has className AND a static style={{}}; use one styling method",
    "inline-sx": "inline sx={{}} object; use a Record<string, SxProps<Theme>> style dictionary",
    "typography-color-override": "<Typography> color set via style/sx; use color=\"text.secondary\" etc.",
    "hardcoded-radius": "numeric borderRadius; use UI_TOKENS.shape or var(--borderRadius, 4px)",
    "inline-token-literal": "raw var(--token, #hex) outside src/tokens; use UI_TOKENS or co-located CSS",
    "token-fallback-drift": "token fallback differs from the canonical value in src/tokens/ui.ts",
    "orphan-css-class": "CSS class is never referenced in source",
    "duplicate-css-class": "same top-level class is defined in more than one CSS file",
    "css-important": "!important in CSS",
    "css-root-scope": ":root declared in component CSS",
    "css-mui-override": ".Mui* class targeted from CSS",
    "css-font-family": "font-family redeclared (host shell owns the font stack)",
    "css-hardcoded-radius": "border-radius in px without var(--borderRadius*)",
    "css-baseline": "<CssBaseline /> mounted inside a guest widget",
    "deep-mui-import": "deep @mui/material/<Component> import; import from the package root",
    "deprecated-input-props": "inputProps= is deprecated in MUI v7; use slotProps.htmlInput",
    "theme-hardcoded-palette": "createTheme hardcodes palette colors or overrides Typography color",
    "file-too-large": "source file exceeds the 250-line ceiling",
} as const;

export type RuleId = keyof typeof RULES;

export interface Violation {
    rule: RuleId;
    file: string;
    line: number;
    detail: string;
}

interface Location {
    file: string;
    line: number;
}

export interface AuditContext {
    canonical: Map<string, string>;
    usedTokens: Set<string>;
    cssClasses: Map<string, Location[]>;
    topLevelClasses: Map<string, Location[]>;
    violations: Violation[];
}

const MAX_LINES = 250;
const TOKEN_VAR = /var\(\s*--([\w-]+)\s*,\s*(#[0-9a-fA-F]{3,8})\s*\)/g;
const COLOR_LITERAL = /#[0-9a-fA-F]{3,8}\b|rgba?\(/;

const normalizeHex = (hex: string): string => {
    const h = hex.toLowerCase();
    return h.length === 4 ? `#${h[1]}${h[1]}${h[2]}${h[2]}${h[3]}${h[3]}` : h;
};

export function readCanonicalFallbacks(uiTokensSource: string): Map<string, string> {
    const canonical = new Map<string, string>();
    for (const [, name, hex] of uiTokensSource.matchAll(TOKEN_VAR)) {
        if (!canonical.has(name)) canonical.set(name, normalizeHex(hex));
    }
    return canonical;
}

export function createContext(canonical = new Map<string, string>()): AuditContext {
    return { canonical, usedTokens: new Set(), cssClasses: new Map(), topLevelClasses: new Map(), violations: [] };
}

const push = (map: Map<string, Location[]>, key: string, loc: Location): void => {
    const list = map.get(key) ?? [];
    if (!list.some(l => l.file === loc.file)) list.push(loc);
    map.set(key, list);
};

function checkTokenText(ctx: AuditContext, { file, line }: Location, text: string, flagLiteral: boolean): void {
    for (const [match, name, hex] of text.matchAll(TOKEN_VAR)) {
        if (flagLiteral) ctx.violations.push({ rule: "inline-token-literal", file, line, detail: match });
        const expected = ctx.canonical.get(name);
        if (expected && expected !== normalizeHex(hex)) {
            ctx.violations.push({ rule: "token-fallback-drift", file, line, detail: `${match} (canonical ${expected})` });
        }
    }
}

const isStaticExpr = (e: ts.Expression): boolean => {
    if (ts.isParenthesizedExpression(e) || ts.isAsExpression(e)) return isStaticExpr(e.expression);
    if (ts.isStringLiteralLike(e) || ts.isNumericLiteral(e)) return true;
    if (e.kind === ts.SyntaxKind.TrueKeyword || e.kind === ts.SyntaxKind.FalseKeyword) return true;
    if (ts.isPrefixUnaryExpression(e)) return ts.isNumericLiteral(e.operand);
    if (ts.isTemplateExpression(e)) return e.templateSpans.every(s => isStaticExpr(s.expression));
    if (ts.isPropertyAccessExpression(e)) {
        let root: ts.Expression = e;
        while (ts.isPropertyAccessExpression(root)) root = root.expression;
        return ts.isIdentifier(root) && root.text.endsWith("_TOKENS");
    }
    return false;
};

const propName = (name: ts.PropertyName): string =>
    ts.isIdentifier(name) || ts.isStringLiteral(name) ? name.text : "";

const objectProps = (obj: ts.ObjectLiteralExpression): ts.PropertyAssignment[] =>
    obj.properties.filter(ts.isPropertyAssignment);

const attrExpr = (attr: ts.JsxAttribute | undefined): ts.Expression | undefined =>
    attr?.initializer && ts.isJsxExpression(attr.initializer) ? attr.initializer.expression : undefined;

const hasDescendant = (node: ts.Node, test: (n: ts.Node) => boolean): boolean =>
    test(node) || (ts.forEachChild(node, c => (hasDescendant(c, test) ? true : undefined)) ?? false);

const isNonZeroLength = (e: ts.Expression): boolean =>
    (ts.isNumericLiteral(e) && Number(e.text) !== 0) || (ts.isStringLiteral(e) && /^[1-9][\d.]*px$/.test(e.text));

function checkJsxElement(ctx: AuditContext, file: string, line: number, el: ts.JsxOpeningLikeElement): void {
    const tag = el.tagName.getText();
    const attrs = el.attributes.properties.filter(ts.isJsxAttribute);
    const attr = (name: string) => attrs.find(a => a.name.getText() === name);
    const add = (rule: RuleId, detail: string) => ctx.violations.push({ rule, file, line, detail });

    const style = attrExpr(attr("style"));
    const styleObj = style && ts.isObjectLiteralExpression(style) ? style : undefined;
    if (styleObj) {
        const staticKeys = objectProps(styleObj)
            .filter(p => isStaticExpr(p.initializer))
            .map(p => propName(p.name));
        if (staticKeys.length > 0) {
            add("inline-static-style", `<${tag}> ${staticKeys.join(", ")}`);
            if (attr("className")) add("mixed-class-and-style", `<${tag}>`);
        }
    }
    const sx = attrExpr(attr("sx"));
    const sxObj = sx && ts.isObjectLiteralExpression(sx) ? sx : undefined;
    if (sx && (sxObj || ts.isArrayLiteralExpression(sx))) add("inline-sx", `<${tag}>`);
    if (tag === "Typography") {
        const setsColor = [styleObj, sxObj].some(o => o && objectProps(o).some(p => propName(p.name) === "color"));
        if (setsColor) add("typography-color-override", "<Typography>");
    }
    if (attr("inputProps")) add("deprecated-input-props", `<${tag}>`);
    if (tag === "CssBaseline") add("css-baseline", "<CssBaseline />");
}

export function auditSource(ctx: AuditContext, file: string, text: string): void {
    const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    const lineOf = (n: ts.Node) => sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1;
    const flagLiteral = !file.startsWith("src/tokens/");
    const lineCount = text.split("\n").length;
    if (lineCount > MAX_LINES) ctx.violations.push({ rule: "file-too-large", file, line: 1, detail: `${lineCount} lines` });

    const visit = (node: ts.Node): void => {
        if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
            const spec = node.moduleSpecifier.text;
            if (/^@mui\/material\/(?!styles$)/.test(spec)) {
                ctx.violations.push({ rule: "deep-mui-import", file, line: lineOf(node), detail: spec });
            }
        } else if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
            checkJsxElement(ctx, file, lineOf(node), node);
        } else if (ts.isPropertyAssignment(node)) {
            const name = propName(node.name);
            const add = (rule: RuleId, detail: string) => ctx.violations.push({ rule, file, line: lineOf(node), detail });
            if (name === "borderRadius" && isNonZeroLength(node.initializer)) add("hardcoded-radius", node.initializer.getText(sf));
            if (name === "palette" && hasDescendant(node.initializer, n => ts.isStringLiteralLike(n) && COLOR_LITERAL.test(n.text))) {
                add("theme-hardcoded-palette", "palette contains hardcoded colors");
            }
            if (name === "MuiTypography" && hasDescendant(node.initializer, n => ts.isPropertyAssignment(n) && propName(n.name) === "color")) {
                add("theme-hardcoded-palette", "MuiTypography color override blocks color= props");
            }
        }
        if (ts.isStringLiteralLike(node) || ts.isTemplateHead(node) || ts.isTemplateMiddle(node) || ts.isTemplateTail(node)) {
            for (const token of node.text.split(/[^\w-]+/)) if (token) ctx.usedTokens.add(token);
            checkTokenText(ctx, { file, line: lineOf(node) }, node.text, flagLiteral);
        }
        ts.forEachChild(node, visit);
    };
    visit(sf);
}

export function auditCss(ctx: AuditContext, file: string, text: string): void {
    const clean = text.replace(/\/\*[\s\S]*?\*\//g, m => m.replace(/[^\n]/g, " "));
    const lineAt = (index: number) => clean.slice(0, index).split("\n").length;
    const add = (rule: RuleId, index: number, detail: string) => ctx.violations.push({ rule, file, line: lineAt(index), detail });

    for (const m of clean.matchAll(/([^{};]+)\{/g)) {
        const selector = m[1].trim();
        const index = (m.index ?? 0) + m[0].indexOf(selector);
        if (selector.startsWith("@") || /^(from|to|[\d.]+%)\b/.test(selector)) continue;
        if (/:root\b/.test(selector)) add("css-root-scope", index, selector);
        for (const [, cls] of selector.matchAll(/\.(-?[_a-zA-Z][\w-]*)/g)) {
            if (cls.startsWith("Mui")) add("css-mui-override", index, selector);
            else push(ctx.cssClasses, cls, { file, line: lineAt(index) });
        }
        for (const part of selector.split(",")) {
            const top = /^\.([\w-]+)(::?[\w-]+)*$/.exec(part.trim());
            if (top) push(ctx.topLevelClasses, top[1], { file, line: lineAt(index) });
        }
    }
    for (const m of clean.matchAll(/([\w-]+)\s*:\s*([^;{}]+)(?=[;}])/g)) {
        const [, prop, value] = m;
        const index = m.index ?? 0;
        if (value.includes("!important")) add("css-important", index, `${prop}: ${value.trim()}`);
        if (prop === "font-family" && !/codeFont|monospace/.test(value)) add("css-font-family", index, value.trim());
        if (prop === "border-radius") {
            let bare = value;
            while (/var\([^()]*\)/.test(bare)) bare = bare.replace(/var\([^()]*\)/g, "");
            if (/\b[1-9][\d.]*px/.test(bare)) add("css-hardcoded-radius", index, value.trim());
        }
    }
    for (const m of clean.matchAll(TOKEN_VAR)) checkTokenText(ctx, { file, line: lineAt(m.index ?? 0) }, m[0], false);
}

export function finalize(ctx: AuditContext): Violation[] {
    for (const [cls, locations] of ctx.cssClasses) {
        if (ctx.usedTokens.has(cls)) continue;
        for (const loc of locations) ctx.violations.push({ rule: "orphan-css-class", ...loc, detail: `.${cls}` });
    }
    for (const [cls, locations] of ctx.topLevelClasses) {
        if (locations.length < 2) continue;
        const files = locations.map(l => l.file).join(", ");
        for (const loc of locations) ctx.violations.push({ rule: "duplicate-css-class", ...loc, detail: `.${cls} in ${files}` });
    }
    return ctx.violations;
}

const walk = (dir: string): string[] =>
    readdirSync(dir).flatMap(name => {
        const full = join(dir, name);
        return statSync(full).isDirectory() ? walk(full) : [full];
    });

export function runAudit(root = process.cwd()): Violation[] {
    const toRel = (p: string) => relative(root, p).split(sep).join("/");
    const files = walk(join(root, "src")).map(toRel).filter(f => !/\.test\.tsx?$/.test(f) && !f.endsWith(".d.ts"));
    const tokensFile = join(root, "src/tokens/ui.ts");
    const ctx = createContext(existsSync(tokensFile) ? readCanonicalFallbacks(readFileSync(tokensFile, "utf8")) : new Map());
    for (const file of files) {
        const text = readFileSync(join(root, file), "utf8");
        if (/\.tsx?$/.test(file)) auditSource(ctx, file, text);
        else if (file.endsWith(".css")) auditCss(ctx, file, text);
    }
    return finalize(ctx);
}
