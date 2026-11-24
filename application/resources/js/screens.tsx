import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ApiError, errorMessage, request, workspacePaths, workspaceSchema } from './api';
import type { Session } from './api';
import { login, logout, replaceSession, useSession } from './auth';

function ThemeToggle() {
    const [theme, setTheme] = useState(() => document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
    function toggle() {
        const next = theme === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.theme = next;
        setTheme(next);
        try { localStorage.setItem('pos-theme', next); } catch { /* The theme still works when storage is unavailable. */ }
    }
    return <button className="button button-secondary theme-toggle" type="button" onClick={toggle} aria-pressed={theme === 'dark'}>
        <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
            {theme === 'dark' ? <path d="M20.8 13A9 9 0 0 1 11 3.2 9 9 0 1 0 20.8 13Z" /> : <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></>}
        </svg>
        Tema gelap
    </button>;
}

function Heading({ children }: { children: ReactNode }) {
    const heading = useRef<HTMLHeadingElement>(null);
    const { pathname } = useLocation();
    useEffect(() => { heading.current?.focus(); }, [pathname]);
    return <h1 ref={heading} tabIndex={-1}>{children}</h1>;
}

function Shell({ children }: { children: ReactNode }) {
    return <div className="account-shell">
        <a className="skip-link" href="#main">Lewati ke konten</a>
        <header className="account-header"><p>Ruang kerja bengkel</p><ThemeToggle /></header>
        <main id="main" className="account-main">{children}</main>
    </div>;
}

function Message({ title, children, retry, pending = false }: { title: string; children?: ReactNode; retry?: () => void; pending?: boolean }) {
    return <Shell><section className="state-panel" aria-busy={pending}>
        <Heading>{title}</Heading>
        {children ? <div className="muted state-description" role={pending ? 'status' : undefined}>{children}</div> : null}
        {retry ? <button type="button" className="button button-primary" onClick={retry}>Coba lagi</button> : null}
    </section></Shell>;
}

const loginSchema = z.object({
    username: z.string().trim().min(1, 'Masukkan username.'),
    password: z.string().min(1, 'Masukkan password.'),
});
type LoginValues = z.infer<typeof loginSchema>;

const permissionLabels: Record<string, string> = {
    'workspace.owner': 'Akses ruang kerja Owner',
    'workspace.teknisi': 'Akses ruang kerja Teknisi',
    'workspace.kasir': 'Akses ruang kerja Kasir',
};

function LoginPage() {
    const client = useQueryClient();
    const navigate = useNavigate();
    const location = useLocation();
    const [visible, setVisible] = useState(false);
    const [failure, setFailure] = useState<string | null>(null);
    const errorSummary = useRef<HTMLDivElement>(null);
    const { register, handleSubmit, setError, resetField, formState: { errors, isSubmitting } } = useForm<LoginValues>({
        resolver: zodResolver(loginSchema),
        defaultValues: { username: '', password: '' },
    });
    const expired = (location.state as { expired?: boolean } | null)?.expired === true;

    async function submit(values: LoginValues) {
        setFailure(null);
        try {
            const session = await login(client, values);
            resetField('password');
            navigate(session.workspace, { replace: true });
        } catch (error) {
            if (error instanceof ApiError && error.status === 422) {
                for (const field of ['username', 'password'] as const) {
                    const message = error.errors[field]?.[0];
                    if (message) setError(field, { type: 'server', message });
                }
            }
            setFailure(error instanceof ApiError && error.status === 422 ? 'Username atau password salah.' : errorMessage(error));
        }
    }
    useEffect(() => { if (failure) errorSummary.current?.focus(); }, [failure]);

    return <div className="login-layout">
        <a className="skip-link" href="#main">Lewati ke form masuk</a>
        <aside className="login-identity" aria-label="Tentang ruang kerja">
            <p className="identity-label">Bengkel AC mobil</p>
            <div className="identity-copy"><p className="identity-title">Ruang kerja bengkel</p>
                <p>Akses untuk Owner, Teknisi, dan Kasir dikelola melalui akun bengkel.</p>
            </div>
            <p className="identity-footer">Gunakan akun Anda sendiri saat bekerja.</p>
        </aside>
        <div className="login-content">
            <div className="login-toolbar"><ThemeToggle /></div>
            <main id="main" className="login-main">
                <div className="login-form-container">
                    <Heading>Masuk ke ruang kerja</Heading>
                    <p className="muted login-description">Masukkan username dan password akun Anda.</p>
                    {expired && !failure ? <p className="notice" role="status">Sesi telah berakhir. Silakan masuk kembali.</p> : null}
                    <form noValidate onSubmit={handleSubmit(submit)} aria-busy={isSubmitting}>
                        {failure ? <div className="form-error" role="alert" ref={errorSummary} tabIndex={-1}>{failure}</div> : null}
                        <div className="field">
                            <label htmlFor="username">Username</label>
                            <input id="username" autoComplete="username" autoCapitalize="none" spellCheck={false} required readOnly={isSubmitting}
                                aria-invalid={Boolean(errors.username)} aria-describedby={errors.username ? 'username-error' : undefined} {...register('username')} />
                            {errors.username ? <p className="field-error" id="username-error">{errors.username.message}</p> : null}
                        </div>
                        <div className="field">
                            <label htmlFor="password">Password</label>
                            <div className="password-control">
                                <input id="password" type={visible ? 'text' : 'password'} autoComplete="current-password" required readOnly={isSubmitting}
                                    aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? 'password-error' : undefined} {...register('password')} />
                                <button className="password-toggle" type="button" aria-label={visible ? 'Sembunyikan password' : 'Tampilkan password'}
                                    aria-pressed={visible} aria-controls="password" onClick={() => setVisible(!visible)} disabled={isSubmitting}>
                                    <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" />
                                        {visible ? <path d="m3 3 18 18" /> : null}
                                    </svg>
                                </button>
                            </div>
                            {errors.password ? <p className="field-error" id="password-error">{errors.password.message}</p> : null}
                        </div>
                        <button className="button button-primary login-submit" type="submit" disabled={isSubmitting}>
                            {isSubmitting ? 'Sedang masuk…' : 'Masuk'}
                        </button>
                        <p className="submission-status" role="status">{isSubmitting ? 'Memeriksa akun. Tunggu sebentar.' : ''}</p>
                    </form>
                    <p className="login-help muted">Belum memiliki akun atau kesulitan masuk? Hubungi Owner.</p>
                </div>
            </main>
        </div>
    </div>;
}

function LogoutButton() {
    const client = useQueryClient();
    const navigate = useNavigate();
    const [pending, setPending] = useState(false);
    const [failure, setFailure] = useState<string | null>(null);
    const summary = useRef<HTMLParagraphElement>(null);
    useEffect(() => { if (failure) summary.current?.focus(); }, [failure]);

    async function leave() {
        if (pending) return;
        setPending(true);
        setFailure(null);
        try {
            await logout(client);
            navigate('/login', { replace: true });
        } catch (error) {
            setFailure(`Belum berhasil keluar. ${errorMessage(error)}`);
        } finally {
            setPending(false);
        }
    }
    return <div className="logout-action">
        <button type="button" className="button button-secondary" onClick={() => void leave()} disabled={pending} aria-describedby={failure ? 'logout-error' : undefined}>
            {pending ? 'Sedang keluar…' : 'Keluar'}
        </button>
        {failure ? <p className="form-error" id="logout-error" role="alert" tabIndex={-1} ref={summary}>{failure}</p> : null}
    </div>;
}

function WorkspacePage({ session, workspace }: { session: Session; workspace: string }) {
    const client = useQueryClient();
    const result = useQuery({
        queryKey: ['workspace', session.user.id, workspace],
        queryFn: async ({ signal }) => {
            const data = workspaceSchema.parse(await request(`/api/workspaces/${workspace}`, { signal }));
            if (data.user.id !== session.user.id || data.user.roles.join('|') !== session.user.roles.join('|')) {
                await client.invalidateQueries({ queryKey: ['session'] });
                throw new ApiError(409, 'Identitas akun berubah. Muat ulang informasi akun.');
            }
            return data;
        },
        retry: false,
        refetchOnWindowFocus: 'always',
    });
    const expired = result.error instanceof ApiError && (result.error.status === 401 || result.error.status === 419);
    useEffect(() => { if (expired) void replaceSession(client, null); }, [client, expired]);
    if (expired) return <Navigate to="/login" replace state={{ expired: true }} />;
    if (result.isPending) return <Message title="Memuat akun" pending>Memeriksa akses ruang kerja Anda.</Message>;
    if (result.error instanceof ApiError && result.error.status === 403) return <Shell>
        <section className="state-panel"><p className="status-code">403</p><Heading>Akses tidak diizinkan</Heading>
            <p className="muted">Akun Anda tidak memiliki akses ke ruang kerja ini.</p>
            <Link className="button button-primary" to={session.workspace}>Kembali ke akun saya</Link>
            <LogoutButton />
        </section>
    </Shell>;
    if (result.isError) return <Message title="Akun belum dapat dimuat" retry={() => void result.refetch()}>{errorMessage(result.error)}</Message>;
    const account = result.data;
    return <Shell>
        <div className="account-title"><div><Heading>Ruang kerja {workspace.charAt(0).toUpperCase() + workspace.slice(1)}</Heading>
            <p className="muted">Informasi akun dan akses Anda saat ini.</p></div><LogoutButton /></div>
        <section className="account-section" aria-labelledby="account-heading">
            <h2 id="account-heading">Akun Anda</h2>
            <dl className="account-details">
                <div><dt>Nama</dt><dd>{account.user.name}</dd></div>
                <div><dt>Username</dt><dd>{account.user.username}</dd></div>
                <div><dt>Peran</dt><dd>{account.user.roles.join(', ')}</dd></div>
            </dl>
        </section>
        <section className="account-section" aria-labelledby="permissions-heading">
            <h2 id="permissions-heading">Hak akses akun</h2>
            <p className="muted">Daftar izin yang diberikan pada akun Anda oleh server.</p>
            {account.permissions.length ? <ul className="permission-list">{account.permissions.map((permission) => <li key={permission}>{permissionLabels[permission] ?? permission}</li>)}</ul>
                : <p className="empty-permissions">Tidak ada izin tambahan pada akun ini.</p>}
        </section>
    </Shell>;
}

export function App() {
    useEffect(() => {
        const root = document.documentElement;
        function pointer() { root.dataset.inputModality = 'pointer'; }
        function keyboard(event: KeyboardEvent) { if (event.key === 'Tab') root.dataset.inputModality = 'keyboard'; }
        document.addEventListener('pointerdown', pointer, true);
        document.addEventListener('keydown', keyboard, true);
        return () => {
            document.removeEventListener('pointerdown', pointer, true);
            document.removeEventListener('keydown', keyboard, true);
        };
    }, []);
    const session = useSession();
    const location = useLocation();
    if (session.isPending) return <Message title="Memeriksa sesi" pending>Menyiapkan akses akun Anda.</Message>;
    if (session.isError) return <Message title="Sesi belum dapat diperiksa" retry={() => void session.refetch()}>{errorMessage(session.error)}</Message>;
    if (!session.data) return <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace state={{ expired: location.pathname.startsWith('/workspace/') }} />} />
    </Routes>;
    const currentSession = session.data;
    return <Routes>
        <Route path="/" element={<Navigate to={currentSession.workspace} replace />} />
        <Route path="/login" element={<Navigate to={currentSession.workspace} replace />} />
        {workspacePaths.map((path) => <Route key={path} path={path} element={<WorkspacePage session={currentSession} workspace={path.split('/')[2] ?? ''} />} />)}
        <Route path="*" element={<Shell><section className="state-panel"><Heading>Halaman tidak ditemukan</Heading><Link className="button button-primary" to={currentSession.workspace}>Kembali ke akun saya</Link></section></Shell>} />
    </Routes>;
}
