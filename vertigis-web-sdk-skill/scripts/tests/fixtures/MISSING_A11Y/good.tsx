import { Box, IconButton, TextField } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

export const Close = ({ onClose }: { onClose: () => void }) => (
    <Box>
        <IconButton aria-label="Close" onClick={onClose}><CloseIcon /></IconButton>
        <TextField label="Name" />
        <Box role="button" tabIndex={0} onClick={onClose} onKeyDown={onClose} />
    </Box>
);
