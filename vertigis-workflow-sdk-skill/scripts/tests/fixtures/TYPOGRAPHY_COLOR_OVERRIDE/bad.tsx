import { Typography } from "@mui/material";

export const Title = ({ tone }: { tone: string }) => (
    <Typography variant="h6" style={{ color: tone }}>Title</Typography>
);
