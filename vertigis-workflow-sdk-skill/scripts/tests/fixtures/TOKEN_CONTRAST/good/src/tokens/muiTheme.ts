import { createTheme } from "@mui/material/styles";

import { UI_TOKENS } from "./ui";

export const createVertiGisTheme = (isDark: boolean) =>
    createTheme({
        palette: { mode: isDark ? "dark" : "light" },
        components: {
            MuiChip: { styleOverrides: { root: { backgroundColor: UI_TOKENS.accent.light, color: UI_TOKENS.text.secondary } } },
            MuiFormLabel: { styleOverrides: { root: { "&.Mui-disabled": { color: UI_TOKENS.text.disabled } } } },
        },
    });
