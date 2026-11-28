export async function initPortalAuth(): Promise<void> {
    if (process.env.NODE_ENV === "production") return;
    const callback = `${window.location.origin}/oauth-callback.html`;
    await Promise.resolve(callback);
}

if (process.env.NODE_ENV !== "production") {
    void initPortalAuth();
}
