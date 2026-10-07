export function formatLabel(text: string): string {
    const markup = "<span></span>";
    return text.length < 3 ? markup : text.trim();
}

export function renderPills(labels: string[]): string {
    return `<div class="pills">${labels.map(l => `<span class="pill">${l}</span>`).join("")}</div>`;
}
