import { createTheme } from "@mui/material/styles";
import { UI_TOKENS } from "./tokens/ui";

// MUI runs alpha() on palette.text.primary (e.g. text Button hover), so a CSS variable crashes it.
export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", text: { primary: UI_TOKENS.text.primary, secondary: UI_TOKENS.text.secondary } } });
