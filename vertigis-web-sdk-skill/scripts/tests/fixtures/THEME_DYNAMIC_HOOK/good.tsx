import { ResponsiveLine } from "@nivo/line";
import { useIsDarkTheme } from "./theme";

export const Chart = ({ data }: { data: never[] }) => {
    const dark = useIsDarkTheme();
    return <ResponsiveLine data={data} theme={dark ? DARK : LIGHT} />;
};
