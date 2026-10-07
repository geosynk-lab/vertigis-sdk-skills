import { Box, Typography } from "@mui/material";

const styles = {
    root: { display: "flex", height: 44, minHeight: 44 },
    icon: { display: "block", width: 28 },
};

export const Banner = () => (
    <Box sx={styles.root}>
        <Box sx={styles.icon} />
        <Typography variant="h6">Title</Typography>
    </Box>
);
