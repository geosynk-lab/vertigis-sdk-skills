import { createTheme } from "@mui/material/styles";
import { UI_TOKENS } from "./tokens/ui";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", background: { default: UI_TOKENS.surface.primary, paper: UI_TOKENS.surface.secondary } } });
