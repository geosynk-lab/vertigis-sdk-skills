import { createTheme } from "@mui/material/styles";
import { useIsDarkTheme } from "./useIsDarkTheme";

export function useWidgetTheme() {
    const isDark = useIsDarkTheme();
    return createTheme({
        palette: { mode: isDark ? "dark" : "light" },
        typography: { fontFamily: "inherit" },
    });
}
