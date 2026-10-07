import { Typography } from "@mui/material";
import { LayoutElement } from "@vertigis/web/components";
import type { LayoutElementProperties } from "@vertigis/web/components";
import { observer } from "mobx-react-lite";
import type ClockModel from "./ClockModel";

const Clock = observer((props: LayoutElementProperties<ClockModel>) => {
    return (
            <Typography variant="body2">{props.model.time}</Typography>
    );
});

export default Clock;
