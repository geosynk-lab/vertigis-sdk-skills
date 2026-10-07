import { Paper } from "@mui/material";

export const Preview = ({ src, alt }: { src: string; alt: string }) => (
    <Paper variant="outlined" sx={{ overflow: "hidden" }}>
        <img src={src} alt={alt} style={{ width: "100%", display: "block" }} />
    </Paper>
);
