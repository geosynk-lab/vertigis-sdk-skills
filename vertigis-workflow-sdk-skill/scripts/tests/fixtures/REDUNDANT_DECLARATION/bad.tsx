import { Box, Typography } from "@mui/material";

const styles = {
    root: { display: "flex", height: 44, minHeight: 44, color: "inherit", letterSpacing: "-0.01em" },
    icon: { display: "block", width: 28 },
    title: { color: "inherit" },
};

export const Banner = () => (
    <Box sx={styles.root}>
        <Box sx={styles.icon} />
        <Typography variant="h6" sx={styles.title}>Title</Typography>
    </Box>
);
