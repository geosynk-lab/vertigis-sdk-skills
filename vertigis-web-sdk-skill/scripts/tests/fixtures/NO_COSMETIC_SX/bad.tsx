import { Card, Typography } from "@mui/material";

const styles = {
    card: { p: 2, bgcolor: "background.paper", boxShadow: "none" },
};

export const Status = ({ status }: { status: string }) => (
    <Card sx={styles.card}>
        <Typography sx={{ fontWeight: 600, color: "var(--secondaryForeground)" }}>{status}</Typography>
    </Card>
);
