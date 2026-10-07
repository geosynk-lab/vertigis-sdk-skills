import { createTheme } from "@mui/material/styles";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", primary: { main: "#007ac2" } } });
