import { Typography } from "@mui/material";
import { LayoutElement } from "@vertigis/web/components";
import type { LayoutElementProperties } from "@vertigis/web/components";
import { observer } from "mobx-react-lite";
import { ErrorBoundary } from "./ErrorBoundary";
import type BadgeModel from "./BadgeModel";

const Badge = observer((props: LayoutElementProperties<BadgeModel>) => {
    return (
            <ErrorBoundary>
            <LayoutElement {...props}>
                <Typography variant="body2">{props.model.time}</Typography>
            </LayoutElement>
            </ErrorBoundary>
    );
});

export default Badge;
