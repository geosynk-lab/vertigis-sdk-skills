import esriConfig from "@arcgis/core/config";

export function initPortalAuth(): void {
    esriConfig.portalUrl = "https://gis.example.com/portal";
}
