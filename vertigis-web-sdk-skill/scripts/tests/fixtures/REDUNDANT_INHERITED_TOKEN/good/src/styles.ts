import type { SxProps, Theme } from "@mui/material";
import { UI_TOKENS } from "./tokens/ui";

export const PANEL_CLASSES = "Panel Panel-header Panel-note";

export const styles: Record<string, SxProps<Theme>> = {
    card: { bgcolor: UI_TOKENS.surface.secondary },
};
