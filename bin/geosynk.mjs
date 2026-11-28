#!/usr/bin/env node
/**
 * geosynk: commands for projects made with the Geosynk VertiGIS skills.
 *
 *   npx -y github:geosynk-lab/vertigis-sdk-skills vertigis-web upgrade [--dry-run] [--path DIR] [--allow-dirty]
 *   npx -y github:geosynk-lab/vertigis-sdk-skills vertigis-workflow upgrade [...]
 *
 * The work is done by <skill>/scripts/upgrade_project.py (Python 3.10+, standard library only).
 */
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS = { "vertigis-web": "vertigis-web-sdk-skill", "vertigis-workflow": "vertigis-workflow-sdk-skill" };
const COMMANDS = { upgrade: "upgrade_project.py" };
const [target, command, ...rest] = process.argv.slice(2);

if (!SKILLS[target] || !COMMANDS[command]) {
    console.error(`usage: geosynk <${Object.keys(SKILLS).join("|")}> <${Object.keys(COMMANDS).join("|")}> [options]`);
    console.error("  upgrade   bring a project made with the skill up to this version (try --dry-run first)");
    process.exit(target === "--help" || target === "-h" ? 0 : 2);
}
const script = join(ROOT, SKILLS[target], "scripts", COMMANDS[command]);
for (const python of ["python3", "python"]) {
    const run = spawnSync(python, [script, ...rest], { stdio: "inherit" });
    if (run.error?.code === "ENOENT") continue;
    process.exit(run.status ?? 1);
}
console.error("geosynk needs Python 3.10+ (python3) on PATH.");
process.exit(1);
