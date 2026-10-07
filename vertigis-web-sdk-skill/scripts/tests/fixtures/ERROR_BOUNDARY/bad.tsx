import { Typography } from "@mui/material";
import { LayoutElement } from "@vertigis/web/components";
import type { LayoutElementProperties } from "@vertigis/web/components";
import { observer } from "mobx-react-lite";
import type ClockModel from "./ClockModel";

const Clock = observer((props: LayoutElementProperties<ClockModel>) => {
    return (
            <LayoutElement {...props}>
                <Typography variant="body2">{props.model.time}</Typography>
            </LayoutElement>
    );
});

export default Clock;
