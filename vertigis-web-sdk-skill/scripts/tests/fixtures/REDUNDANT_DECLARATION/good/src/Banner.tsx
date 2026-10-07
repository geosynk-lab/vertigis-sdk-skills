import { Box, Typography } from "@mui/material";

import "./Banner.css";

const styles = {
    root: { display: "flex", minHeight: 44 },
    icon: { width: 28 },
};

export const Banner = () => (
    <Box className="Banner" sx={styles.root}>
        <Box sx={styles.icon} />
        <Typography variant="h6">Title</Typography>
    </Box>
);
