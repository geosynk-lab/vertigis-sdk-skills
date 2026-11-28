import { Box, IconButton, IconButton as MuiIconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { IconButton as AppIconButton } from "./AppIconButton";

export const Close = ({ onClose }: { onClose: () => void }) => (
    <Box>
        <IconButton onClick={onClose}><CloseIcon /></IconButton>
        <MuiIconButton label="Close" onClick={onClose}><CloseIcon /></MuiIconButton>
        <AppIconButton icon="close" onClick={onClose} />
        <Box onClick={onClose} />
    </Box>
);
