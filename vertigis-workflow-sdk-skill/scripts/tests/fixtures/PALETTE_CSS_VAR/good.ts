import { createTheme } from "@mui/material/styles";
import { ACCENT } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", primary: { main: ACCENT } } });
