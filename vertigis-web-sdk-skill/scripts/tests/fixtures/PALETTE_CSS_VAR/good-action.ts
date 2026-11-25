import { createTheme } from "@mui/material/styles";
import { ITEM_HOVER } from "./tokens";

export const makeTheme = (isDark: boolean) =>
    createTheme({ palette: { mode: isDark ? "dark" : "light", action: { hover: ITEM_HOVER, hoverOpacity: 0.04 } } });
