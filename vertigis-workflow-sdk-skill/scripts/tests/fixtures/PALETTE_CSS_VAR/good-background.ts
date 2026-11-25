import { createTheme } from "@mui/material/styles";
import { SURFACE_DEFAULT, SURFACE_PAPER } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", background: { default: SURFACE_DEFAULT, paper: SURFACE_PAPER } } });
