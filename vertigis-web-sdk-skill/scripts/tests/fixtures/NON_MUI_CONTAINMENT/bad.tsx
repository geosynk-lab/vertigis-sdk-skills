import { Box } from "@mui/material";

export const Preview = ({ src, alt }: { src: string; alt: string }) => (
    <Box sx={{ display: "flex" }}>
        <img src={src} alt={alt} />
    </Box>
);
