import { createTheme } from "@mui/material/styles";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", primary: { main: "var(--primaryAccent)" } } });

// UI_TOKENS values are var(...) strings, so they crash augmentColor() as well.
declare const UI_TOKENS: { accent: { primary: string } };
export const makeTokenTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", primary: { main: UI_TOKENS.accent.primary } } });
