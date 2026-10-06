export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`/api${path}`, {
        ...options,
        headers: { "Content-Type": "application/json", ...options.headers },
    });

    if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Request failed: ${res.status}`);
    }
    return res.status === 204 ? (undefined as T) : res.json();
}