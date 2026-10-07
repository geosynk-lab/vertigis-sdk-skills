import { createTheme } from "@mui/material/styles";
import { TOKENS } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light" }, components: { MuiTypography: { styleOverrides: { root: { color: TOKENS.text } } } } });
