import { Card, CardContent, Stack, Typography } from "@mui/material";

export const Status = ({ status, label }: { status: string; label: string }) => (
    <Card data-status={status}>
        <CardContent>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", minWidth: 0 }}>
                <Typography variant="subtitle2">{label}</Typography>
                <Typography variant="body2" color="text.secondary">{status}</Typography>
            </Stack>
        </CardContent>
    </Card>
);
