import { Box, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

export const Close = ({ onClose }: { onClose: () => void }) => (
    <Box>
        <IconButton onClick={onClose}><CloseIcon /></IconButton>
        <Box onClick={onClose} />
    </Box>
);
