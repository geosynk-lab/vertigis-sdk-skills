import { createTheme } from "@mui/material/styles";
import { TEXT_PRIMARY, TEXT_SECONDARY } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", text: { primary: TEXT_PRIMARY, secondary: TEXT_SECONDARY } } });
