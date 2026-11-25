import { createTheme } from "@mui/material/styles";
import { ACCENT_CONTRAST, tokens } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({
        palette: { mode: isDark ? "dark" : "light", secondary: { contrastText: ACCENT_CONTRAST } },
        components: { MuiDivider: { styleOverrides: { root: { borderColor: tokens.ui.border.divider } } } },
    });
