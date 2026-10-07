import { Box, Stack } from "@mui/material";

export const Row = () => (
    <Stack spacing={1.5}>
        <Box sx={{ p: { xs: 1, md: 2 }, mx: "auto", mt: -0.5, gap: 1 }} />
    </Stack>
);
