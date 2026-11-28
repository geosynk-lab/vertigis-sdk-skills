export async function initPortalAuth(): Promise<void> {
    const callback = `${window.location.origin}/oauth-callback.html`;
    await Promise.resolve(callback);
}

initPortalAuth();
