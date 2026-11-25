import { createTheme } from "@mui/material/styles";
import { DIVIDER } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", divider: DIVIDER } });
