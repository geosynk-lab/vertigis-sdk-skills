import { Box, IconButton, TextField } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { IconButton as AppIconButton } from "./AppIconButton";

export const Close = ({ onClose }: { onClose: () => void }) => (
    <Box>
        <IconButton aria-label="Close" onClick={onClose}><CloseIcon /></IconButton>
        <AppIconButton icon="close" label="Close" onClick={onClose} />
        <TextField label="Name" />
        <Box role="button" tabIndex={0} onClick={onClose} onKeyDown={onClose} />
    </Box>
);
