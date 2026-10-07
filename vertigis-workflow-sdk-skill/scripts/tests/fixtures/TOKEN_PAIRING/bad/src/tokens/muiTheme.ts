import { createTheme } from "@mui/material/styles";

import { UI_TOKENS } from "./ui";

export const createVertiGisTheme = (isDark: boolean) =>
    createTheme({
        palette: { mode: isDark ? "dark" : "light" },
        components: {
            MuiAlert: { styleOverrides: { root: { backgroundColor: UI_TOKENS.status.errorBg, color: UI_TOKENS.text.primary } } },
            MuiFormLabel: { styleOverrides: { root: { color: UI_TOKENS.accent.contrastText } } },
            MuiChip: { styleOverrides: { root: { backgroundColor: UI_TOKENS.text.secondary } } },
        },
    });
