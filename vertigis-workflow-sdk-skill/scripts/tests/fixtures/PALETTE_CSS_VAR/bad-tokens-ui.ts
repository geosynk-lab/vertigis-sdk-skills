import { createTheme } from "@mui/material/styles";
import { tokens } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", secondary: { contrastText: tokens.ui.accent.contrastText } } });
