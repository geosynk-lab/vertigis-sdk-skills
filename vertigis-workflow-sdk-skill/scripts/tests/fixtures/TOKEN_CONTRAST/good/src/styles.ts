import type { SxProps, Theme } from "@mui/material";
import { UI_TOKENS } from "./tokens/ui";

export const PANEL_CLASSES = "Panel-hint";

export const styles: Record<string, SxProps<Theme>> = {
    hint: { bgcolor: UI_TOKENS.accent.light, color: UI_TOKENS.text.secondary },
    off: { color: UI_TOKENS.text.disabled },
};
