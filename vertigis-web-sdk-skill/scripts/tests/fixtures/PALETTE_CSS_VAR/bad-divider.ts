import { createTheme } from "@mui/material/styles";
import { UI_TOKENS } from "./tokens/ui";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", divider: UI_TOKENS.border.divider } });
