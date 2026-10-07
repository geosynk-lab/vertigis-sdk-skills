import type { FormElementProps, FormElementRegistration } from "@vertigis/workflow";
import { Button } from "@mui/material";
import { FormElementErrorBoundary } from "./components/FormElementErrorBoundary";

function Rating(props: FormElementProps<number>) {
    const { visible, enabled } = props;
    if (!visible) return null;
    return <Button disabled={!enabled} onClick={() => props.setValue(1)}>Rate</Button>;
}

const RatingRegistration: FormElementRegistration<FormElementProps<number>> = { component: Rating, id: "Rating" };
export default RatingRegistration;
