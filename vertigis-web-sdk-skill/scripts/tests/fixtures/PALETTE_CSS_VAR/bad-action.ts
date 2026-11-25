import { createTheme } from "@mui/material/styles";
import { UI_TOKENS } from "./tokens/ui";

// MUI runs alpha() on palette.action.* (e.g. hover and selected backgrounds).
export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", action: { hover: UI_TOKENS.control.itemHover, hoverOpacity: 0.04 } } });
