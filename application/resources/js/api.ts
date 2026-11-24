import { z } from 'zod';

const userSchema = z.object({
    id: z.uuid(),
    username: z.string(),
    name: z.string(),
    roles: z.array(z.string()),
});

export const workspacePaths = ['/workspace/owner', '/workspace/teknisi', '/workspace/kasir'] as const;
export const sessionSchema = z.object({
    user: userSchema,
    workspace: z.enum(workspacePaths),
});
export const workspaceSchema = z.object({
    user: userSchema,
    workspace: z.string(),
    permissions: z.array(z.string()),
});
export type Session = z.infer<typeof sessionSchema>;
export type Workspace = z.infer<typeof workspaceSchema>;

const failureSchema = z.object({
    message: z.string().optional(),
    errors: z.record(z.string(), z.array(z.string())).optional(),
});

export class ApiError extends Error {
    constructor(
        public readonly status: number,
        message: string,
        public readonly errors: Record<string, string[]> = {},
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

export async function request(path: string, init: RequestInit = {}): Promise<unknown> {
    const response = await fetch(path, {
        ...init,
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { Accept: 'application/json', ...init.headers },
    });
    if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        const failure = failureSchema.safeParse(body);
        throw new ApiError(
            response.status,
            failure.success ? (failure.data.message ?? 'Permintaan tidak berhasil.') : 'Permintaan tidak berhasil.',
            failure.success ? (failure.data.errors ?? {}) : {},
        );
    }
    if (response.status === 204) return null;
    return response.json();
}

export async function post(path: string, body?: unknown): Promise<unknown> {
    await request('/sanctum/csrf-cookie');
    const cookie = document.cookie.split('; ').find((part) => part.startsWith('XSRF-TOKEN='));
    if (!cookie) throw new ApiError(419, 'Sesi formulir tidak tersedia. Muat ulang halaman, lalu coba lagi.');
    return request(path, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-XSRF-TOKEN': decodeURIComponent(cookie.slice('XSRF-TOKEN='.length)),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
}

export function errorMessage(error: unknown): string {
    if (error instanceof ApiError) {
        if (error.status === 419) return 'Sesi formulir kedaluwarsa. Coba lagi untuk memperbarui sesi.';
        if (error.status === 429) return 'Terlalu banyak percobaan. Tunggu sebentar sebelum mencoba lagi.';
        if (error.status >= 500) return 'Server belum dapat memproses permintaan. Coba lagi nanti.';
        if (error.status === 401) return 'Sesi telah berakhir. Silakan masuk kembali.';
        return error.message;
    }
    if (error instanceof z.ZodError || error instanceof SyntaxError) {
        return 'Respons server tidak dapat dibaca. Muat ulang halaman atau hubungi Owner.';
    }
    return 'Tidak dapat terhubung ke server. Periksa koneksi, lalu coba lagi.';
}
