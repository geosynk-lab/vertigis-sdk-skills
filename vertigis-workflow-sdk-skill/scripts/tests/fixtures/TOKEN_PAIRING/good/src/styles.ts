import type { SxProps, Theme } from "@mui/material";
import { UI_TOKENS } from "./tokens/ui";

export const PANEL_CLASSES = "Panel-badge Panel-badge-count";

export const styles: Record<string, SxProps<Theme>> = {
    banner: {
        bgcolor: UI_TOKENS.status.errorBg,
        color: UI_TOKENS.status.errorFg,
        "& .title": { color: UI_TOKENS.status.errorFg },
    },
    caption: { color: UI_TOKENS.text.secondary },
};
