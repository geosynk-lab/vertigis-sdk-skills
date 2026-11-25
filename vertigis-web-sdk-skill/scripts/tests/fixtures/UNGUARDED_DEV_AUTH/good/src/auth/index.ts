import esriConfig from "@arcgis/core/config";

export function initPortalAuth(): void {
    if (process.env.NODE_ENV === "production") {
        return;
    }
    esriConfig.portalUrl = "https://gis.example.com/portal";
}
