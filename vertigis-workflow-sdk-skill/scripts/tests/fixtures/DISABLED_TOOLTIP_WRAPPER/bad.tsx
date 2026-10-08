import { Button, Tooltip } from "@mui/material";

export const BadTooltip = () => (
    <Tooltip title="Disabled action">
        <Button disabled>Click</Button>
    </Tooltip>
);
