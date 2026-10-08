import { isDarkTheme } from "./utils/themeDetection";
import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
    components: {
        MuiCard: {
            styleOverrides: {
                root: {
                    "&.PunchlistCard-root[data-status='Open']": {
                        borderLeft: "4px solid red",
                    },
                },
            },
        },
    },
});

if (isDarkTheme()) {
    console.log("dark");
}
