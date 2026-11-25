import { createTheme } from "@mui/material/styles";
import { UI_TOKENS } from "./tokens/ui";
import { ACCENT } from "./tokens";

// The palette gets a static colour; the CSS variable goes through styleOverrides.
export const makeTheme = (isDark: boolean) =>
    createTheme({
        palette: { mode: isDark ? "dark" : "light", primary: { main: ACCENT } },
        components: { MuiDivider: { styleOverrides: { root: { borderColor: UI_TOKENS.border.divider } } } },
    });
