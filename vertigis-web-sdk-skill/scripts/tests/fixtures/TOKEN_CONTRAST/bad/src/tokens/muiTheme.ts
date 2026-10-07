import { createTheme } from "@mui/material/styles";

import { UI_TOKENS } from "./ui";

export const createVertiGisTheme = (isDark: boolean) =>
    createTheme({
        palette: { mode: isDark ? "dark" : "light" },
        components: {
            MuiChip: { styleOverrides: { root: { backgroundColor: UI_TOKENS.control.itemHover, color: UI_TOKENS.text.secondary } } },
        },
    });
