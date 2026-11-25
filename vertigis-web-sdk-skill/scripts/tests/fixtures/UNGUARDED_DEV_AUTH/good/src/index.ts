import { initPortalAuth } from "./auth";

if (process.env.NODE_ENV !== "production") {
    initPortalAuth();
}

export default function (): void {}
