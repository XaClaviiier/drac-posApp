import { QueryClient, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError, post, request, sessionSchema } from './api';
import type { Session } from './api';

export const sessionKey = ['session'] as const;

export function createQueryClient(): QueryClient {
    return new QueryClient({
        defaultOptions: {
            queries: { retry: false, networkMode: 'always' },
            mutations: { retry: false, networkMode: 'always' },
        },
    });
}

function sameIdentity(previous: Session | null | undefined, next: Session | null): boolean {
    return previous?.user.id === next?.user.id
        && previous?.workspace === next?.workspace
        && previous?.user.roles.join('|') === next?.user.roles.join('|');
}

async function clearUserData(client: QueryClient): Promise<void> {
    const otherQueries = { predicate: (query: { queryKey: readonly unknown[] }) => query.queryKey[0] !== sessionKey[0] };
    await client.cancelQueries(otherQueries);
    client.removeQueries(otherQueries);
    client.getMutationCache().clear();
}

export async function replaceSession(client: QueryClient, session: Session | null): Promise<void> {
    await client.cancelQueries({ queryKey: sessionKey });
    await clearUserData(client);
    client.setQueryData(sessionKey, session);
}

export function useSession() {
    const client = useQueryClient();
    return useQuery({
        queryKey: sessionKey,
        queryFn: async ({ signal }): Promise<Session | null> => {
            let session: Session | null;
            try {
                session = sessionSchema.parse(await request('/api/session', { signal }));
            } catch (error) {
                if (!(error instanceof ApiError) || error.status !== 401) throw error;
                session = null;
            }
            if (!sameIdentity(client.getQueryData<Session | null>(sessionKey), session)) {
                await clearUserData(client);
            }
            return session;
        },
        retry: false,
        staleTime: 30_000,
        refetchOnWindowFocus: 'always',
    });
}

export async function login(client: QueryClient, credentials: { username: string; password: string }): Promise<Session> {
    const session = sessionSchema.parse(await post('/login', credentials));
    await replaceSession(client, session);
    return session;
}

export async function logout(client: QueryClient): Promise<void> {
    try {
        await post('/logout');
    } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error;
    }
    await replaceSession(client, null);
}
