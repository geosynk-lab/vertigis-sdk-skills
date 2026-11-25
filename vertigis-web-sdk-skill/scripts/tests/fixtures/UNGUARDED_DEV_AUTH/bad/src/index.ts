import { initPortalAuth } from "./auth";

// Runs in production too: registers dev OAuth callbacks and hijacks the host sign-in.
initPortalAuth();

export default function (): void {}
