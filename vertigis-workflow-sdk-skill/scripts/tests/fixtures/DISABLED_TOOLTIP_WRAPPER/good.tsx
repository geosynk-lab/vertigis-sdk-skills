import { Button, Tooltip } from "@mui/material";

export const GoodTooltip = () => (
    <Tooltip title="Disabled action">
        <span>
            <Button disabled>Click</Button>
        </span>
    </Tooltip>
);
