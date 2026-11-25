import { createTheme } from "@mui/material/styles";
import { UI_TOKENS } from "./tokens/ui";

// UI_TOKENS.accent.primary is "var(--primaryAccent, #1a72c4)": augmentColor() cannot parse it.
export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", primary: { main: UI_TOKENS.accent.primary } } });
