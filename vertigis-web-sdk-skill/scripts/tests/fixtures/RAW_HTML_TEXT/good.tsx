import { Typography } from "@mui/material";

export const Label = () => (
    <Typography variant="body2">
        Hello <strong>World</strong>
    </Typography>
);

// A JSX comment is not text content.
export const Actions = ({ ready }: { ready: boolean }) => (
    <span className="Actions-root">
        {/* The icons sit in one row. */}
        {ready && (
            <Typography variant="body2">Done</Typography>
        )}
    </span>
);
