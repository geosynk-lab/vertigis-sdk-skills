import type { SxProps, Theme } from "@mui/material";
import { UI_TOKENS } from "./tokens/ui";

export const PANEL_CLASSES = "Panel-badge";

export const styles: Record<string, SxProps<Theme>> = {
    banner: { bgcolor: UI_TOKENS.status.errorBg, color: UI_TOKENS.text.primary },
    label: { color: UI_TOKENS.accent.contrastText },
    inverted: { bgcolor: UI_TOKENS.text.secondary },
};
