import { createTheme } from "@mui/material/styles";

import { UI_TOKENS } from "./ui";

export const createVertiGisTheme = (isDark: boolean) =>
    createTheme({
        palette: { mode: isDark ? "dark" : "light" },
        components: {
            MuiAlert: {
                styleOverrides: {
                    root: {
                        backgroundColor: UI_TOKENS.status.errorBg,
                        color: UI_TOKENS.status.errorFg,
                        "& .MuiAlert-message": { color: UI_TOKENS.status.errorFg },
                    },
                },
            },
            MuiFormHelperText: { styleOverrides: { root: { color: UI_TOKENS.text.secondary } } },
        },
    });
