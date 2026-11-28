import type { SxProps, Theme } from "@mui/material";
import { UI_TOKENS } from "./tokens/ui";

export const PANEL_CLASSES = "Panel-hint";

export const styles: Record<string, SxProps<Theme>> = {
    hint: { bgcolor: UI_TOKENS.control.itemHover, color: UI_TOKENS.text.secondary },
};
