import { useState } from 'react';
import { QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query';
import type { QueryClient } from '@tanstack/react-query';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createQueryClient, login, logout, useSession } from '../auth';
import { request } from '../api';
import type { Session } from '../api';
import { App } from '../screens';

const owner: Session = { user: { id: '00000000-0000-4000-8000-000000000001', username: 'owner.test', name: 'Akun pertama', roles: ['Owner'] }, workspace: '/workspace/owner' };
const cashier: Session = { user: { id: '00000000-0000-4000-8000-000000000002', username: 'kasir.test', name: 'Akun kedua', roles: ['Kasir'] }, workspace: '/workspace/kasir' };
const fetchMock = vi.fn<typeof fetch>();
const clients: QueryClient[] = [];

function json(body: unknown, status = 200) {
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function mount(path = '/login') {
    const client = createQueryClient();
    clients.push(client);
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>);
    return client;
}

async function enterCredentials() {
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText('Username'), 'owner.test');
    await user.type(screen.getByLabelText('Password', { exact: true }), 'private-test-password');
    await user.click(screen.getByRole('button', { name: 'Masuk' }));
    return user;
}

beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
    fetchMock.mockReset();
    document.cookie = 'XSRF-TOKEN=csrf%3Dtest; Path=/';
});
afterEach(() => {
    for (const client of clients.splice(0)) client.clear();
    vi.unstubAllGlobals();
});

describe('session and login screens', () => {
    it('shows the login form only after a confirmed guest response', async () => {
        fetchMock.mockResolvedValue(json({ message: 'Unauthenticated.' }, 401));
        mount('/workspace/owner');
        expect(await screen.findByRole('heading', { name: 'Masuk ke ruang kerja' })).toBeInTheDocument();
        expect(screen.getByText('Sesi telah berakhir. Silakan masuk kembali.')).toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: 'Ruang kerja Owner' })).not.toBeInTheDocument();
    });

    it('keeps a session network failure distinct from a guest and supports an explicit retry', async () => {
        fetchMock.mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(json({ message: 'Unauthenticated.' }, 401));
        mount();
        expect(await screen.findByRole('heading', { name: 'Sesi belum dapat diperiksa' })).toBeInTheDocument();
        expect(screen.queryByLabelText('Username')).not.toBeInTheDocument();
        expect(fetchMock).toHaveBeenCalledTimes(1);
        await userEvent.click(screen.getByRole('button', { name: 'Coba lagi' }));
        expect(await screen.findByLabelText('Username')).toBeInTheDocument();
    });

    it('shows incorrect credentials without retrying or discarding entered fields', async () => {
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return json({ message: 'Unauthenticated.' }, 401);
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            return json({ message: 'Username atau password salah.' }, 422);
        });
        mount();
        await enterCredentials();
        const error = await screen.findByRole('alert');
        expect(error).toHaveTextContent('Username atau password salah.');
        await waitFor(() => expect(error).toHaveFocus());
        expect(screen.getByLabelText('Username')).toHaveValue('owner.test');
        expect(screen.getByLabelText('Password', { exact: true })).toHaveValue('private-test-password');
        expect(screen.getByRole('button', { name: 'Masuk' })).toBeEnabled();
        expect(fetchMock.mock.calls.filter(([path]) => path === '/login')).toHaveLength(1);
        const options = fetchMock.mock.calls.find(([path]) => path === '/login')?.[1];
        expect(options?.credentials).toBe('same-origin');
        expect(options?.headers).toMatchObject({ 'X-XSRF-TOKEN': 'csrf=test' });
    });

    it('shows a login network error without treating the write as safe to retry automatically', async () => {
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return json({}, 401);
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            throw new TypeError('offline');
        });
        mount();
        await enterCredentials();
        expect(await screen.findByRole('alert')).toHaveTextContent('Tidak dapat terhubung ke server.');
        expect(fetchMock.mock.calls.filter(([path]) => path === '/login')).toHaveLength(1);
    });

    it('keeps an expired login write actionable without automatically replaying credentials', async () => {
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return json({}, 401);
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            return json({ message: 'CSRF token mismatch.' }, 419);
        });
        mount();
        await enterCredentials();
        expect(await screen.findByRole('alert')).toHaveTextContent('Sesi formulir kedaluwarsa.');
        expect(screen.getByRole('button', { name: 'Masuk' })).toBeEnabled();
        expect(fetchMock.mock.calls.filter(([path]) => path === '/login')).toHaveLength(1);
    });

    it('disables submission while the login request is pending', async () => {
        const pendingLogin = Promise.withResolvers<Response>();
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return json({}, 401);
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            return pendingLogin.promise;
        });
        mount();
        await enterCredentials();
        expect(await screen.findByRole('button', { name: 'Sedang masuk…' })).toBeDisabled();
        await act(async () => { pendingLogin.resolve(json({}, 422)); });
        expect(await screen.findByRole('alert')).toBeInTheDocument();
    });

    it('returns server-denied workspace access to the account default instead of offering role switching', async () => {
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return json(cashier);
            if (input === '/api/workspaces/owner') return json({ message: 'Forbidden.' }, 403);
            return json({ ...cashier, permissions: ['workspace.kasir'] });
        });
        mount('/workspace/owner');
        expect(await screen.findByRole('heading', { name: 'Akses tidak diizinkan' })).toBeInTheDocument();
        await userEvent.click(screen.getByRole('link', { name: 'Kembali ke akun saya' }));
        expect(await screen.findByRole('heading', { name: 'Ruang kerja Kasir' })).toBeInTheDocument();
        expect(screen.getByText('Akun kedua')).toBeInTheDocument();
    });

    it('keeps the current account visible when logout fails', async () => {
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return json(owner);
            if (input === '/api/workspaces/owner') return json({ ...owner, permissions: ['workspace.owner'] });
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            return json({ message: 'Unavailable.' }, 503);
        });
        mount('/workspace/owner');
        await userEvent.click(await screen.findByRole('button', { name: 'Keluar' }));
        expect(await screen.findByRole('alert')).toHaveTextContent('Belum berhasil keluar.');
        expect(screen.getByText('Akun pertama')).toBeInTheDocument();
        expect(screen.queryByLabelText('Username')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Keluar' })).toBeEnabled();
    });
});

function PrivateAccountData() {
    const data = useQuery({
        queryKey: ['private-account-data'],
        queryFn: () => request('/api/private-account-data'),
        staleTime: Infinity,
    });
    return <p>{typeof data.data === 'string' ? data.data : 'Loading private account data'}</p>;
}

function SessionConsumer() {
    const client = useQueryClient();
    const session = useSession();
    const [failure, setFailure] = useState(false);
    if (!session.data) return <button onClick={() => void login(client, { username: 'kasir.test', password: 'test-only' })}>Sign in again</button>;
    return <>
        <p>{session.data.user.name}</p>
        <PrivateAccountData key={session.data.user.id} />
        <button onClick={() => void session.refetch()}>Check session</button>
        <button onClick={() => void logout(client).catch(() => setFailure(true))}>Sign out</button>
        {failure ? <p>Sign out failed</p> : null}
    </>;
}

function mountConsumer() {
    const client = createQueryClient();
    clients.push(client);
    render(<QueryClientProvider client={client}><SessionConsumer /></QueryClientProvider>);
}

describe('private cached data lifecycle', () => {
    it('does not show the previous account cached data when restored session identity changes', async () => {
        let current = owner;
        fetchMock.mockImplementation(async (input) => input === '/api/session'
            ? json(current)
            : json(current.user.id === owner.user.id ? 'Private first account' : 'Private second account'));
        mountConsumer();
        expect(await screen.findByText('Private first account')).toBeInTheDocument();
        current = cashier;
        await userEvent.click(screen.getByRole('button', { name: 'Check session' }));
        expect(await screen.findByText('Private second account')).toBeInTheDocument();
        expect(screen.queryByText('Private first account')).not.toBeInTheDocument();
    });

    it('clears private cached data after logout before another account signs in', async () => {
        let current: Session | null = owner;
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return current ? json(current) : json({}, 401);
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            if (input === '/logout') { current = null; return new Response(null, { status: 204 }); }
            if (input === '/login') { current = cashier; return json(cashier); }
            return json(current?.user.id === owner.user.id ? 'Private first account' : 'Private second account');
        });
        mountConsumer();
        expect(await screen.findByText('Private first account')).toBeInTheDocument();
        await userEvent.click(screen.getByRole('button', { name: 'Sign out' }));
        expect(await screen.findByRole('button', { name: 'Sign in again' })).toBeInTheDocument();
        expect(screen.queryByText('Private first account')).not.toBeInTheDocument();
        await userEvent.click(screen.getByRole('button', { name: 'Sign in again' }));
        expect(await screen.findByText('Private second account')).toBeInTheDocument();
        expect(screen.queryByText('Private first account')).not.toBeInTheDocument();
    });

    it('clears expired account data when logout confirms the session already ended', async () => {
        let current: Session | null = owner;
        fetchMock.mockImplementation(async (input) => {
            if (input === '/api/session') return current ? json(current) : json({}, 401);
            if (input === '/sanctum/csrf-cookie') return new Response(null, { status: 204 });
            if (input === '/logout') { current = null; return json({ message: 'Unauthenticated.' }, 401); }
            if (input === '/login') { current = cashier; return json(cashier); }
            return json(current?.user.id === owner.user.id ? 'Private first account' : 'Private second account');
        });
        mountConsumer();
        expect(await screen.findByText('Private first account')).toBeInTheDocument();
        await userEvent.click(screen.getByRole('button', { name: 'Sign out' }));
        expect(await screen.findByRole('button', { name: 'Sign in again' })).toBeInTheDocument();
        expect(screen.queryByText('Private first account')).not.toBeInTheDocument();
        expect(screen.queryByText('Sign out failed')).not.toBeInTheDocument();
        await userEvent.click(screen.getByRole('button', { name: 'Sign in again' }));
        expect(await screen.findByText('Private second account')).toBeInTheDocument();
        expect(screen.queryByText('Private first account')).not.toBeInTheDocument();
    });
});
