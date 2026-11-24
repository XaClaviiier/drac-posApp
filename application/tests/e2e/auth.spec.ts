import { test, expect, request as requestFactory, type Page } from '@playwright/test';
import { readFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

type Role = 'owner' | 'teknisi' | 'kasir';
type Account = { id: string; username: string; password: string };
const accounts = JSON.parse(readFileSync(resolve('../.local/auth-e2e-accounts.json'), 'utf8')) as Record<Role, Account>;

async function login(page: Page, role: Role) {
    await page.goto('/login');
    await page.getByLabel('Username', { exact: true }).fill(accounts[role].username);
    await page.getByLabel('Password', { exact: true }).fill(accounts[role].password);
    await page.getByRole('button', { name: 'Masuk', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/workspace/${role}$`));
    await expect(page.getByText(accounts[role].username, { exact: true })).toBeVisible();
}

for (const role of ['owner', 'teknisi', 'kasir'] as const) {
    test(`login ${role}, server permissions and logout invalidation`, async ({ page, context }) => {
        const errors: string[] = [];
        page.on('pageerror', error => errors.push(error.message));
        await login(page, role);
        const session = await page.request.get('/api/session');
        expect(session.status()).toBe(200);
        const body = await session.json();
        expect(body.user.id).toBe(accounts[role].id);
        expect(body.user).not.toHaveProperty('password');
        expect(body.user).not.toHaveProperty('remember_token');
        for (const workspace of ['owner', 'teknisi', 'kasir']) {
            const response = await page.request.get(`/api/workspaces/${workspace}`);
            expect(response.status()).toBe(role === 'owner' || workspace === role ? 200 : 403);
        }
        const cookies = await context.cookies();
        const sessionCookie = cookies.find(cookie => cookie.name === 'pos_session');
        expect(sessionCookie?.httpOnly).toBe(true);
        expect(sessionCookie?.sameSite).toBe('Lax');
        const replay = await requestFactory.newContext({ baseURL: 'http://127.0.0.1:8089', storageState: { cookies, origins: [] } });
        try {
            await page.getByRole('button', { name: 'Keluar', exact: true }).click();
            await expect(page).toHaveURL(/\/login$/);
            expect((await replay.get('/api/session')).status()).toBe(401);
            await page.goto(`/workspace/${role}`);
            await expect(page).toHaveURL(/\/login$/);
            expect(errors).toEqual([]);
        } finally {
            await replay.dispose();
        }
    });
}

test('wrong password stays on login with generic error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Username', { exact: true }).fill(accounts.kasir.username);
    await page.getByLabel('Password', { exact: true }).fill('deliberately-incorrect-fixture-input');
    await page.getByRole('button', { name: 'Masuk', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('Username atau password salah.');
    await expect(page).toHaveURL(/\/login$/);
    expect((await page.request.get('/api/session')).status()).toBe(401);
});

test('HTTP CSRF rejects credential writes without token', async ({ request }) => {
    await request.get('/sanctum/csrf-cookie');
    const response = await request.post('/login', { data: { username: accounts.owner.username, password: accounts.owner.password } });
    expect(response.status()).toBe(419);
    expect((await request.get('/api/session')).status()).toBe(401);
});

test('login visual, keyboard, theme and mobile reflow', async ({ page }) => {
    mkdirSync('test-results', { recursive: true });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/login');
    await page.evaluate(() => document.fonts.ready);
    await expect(page.getByLabel('Username', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.fonts.check('400 16px Poppins'))).toBe(true);
    expect(await page.evaluate(() => getComputedStyle(document.activeElement!).outlineStyle)).toBe('none');
    await page.screenshot({ path: 'test-results/auth-desktop-light.png', fullPage: true });
    await page.keyboard.press('Tab');
    const focusOutline = await page.evaluate(() => getComputedStyle(document.activeElement!).outlineStyle);
    expect(focusOutline).not.toBe('none');
    await page.getByRole('button', { name: /tema|gelap|terang/i }).click();
    await page.evaluate(() => Promise.all(document.getAnimations().map(animation => animation.finished.catch(() => undefined))));
    await page.screenshot({ path: 'test-results/auth-desktop-dark.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.getByRole('button', { name: 'Masuk', exact: true })).toBeVisible();
    await page.screenshot({ path: 'test-results/auth-mobile-dark.png', fullPage: true });
    await page.getByRole('button', { name: /tema|gelap|terang/i }).click();
    await page.evaluate(() => Promise.all(document.getAnimations().map(animation => animation.finished.catch(() => undefined))));
    await page.screenshot({ path: 'test-results/auth-mobile-light.png', fullPage: true });
    await login(page, 'teknisi');
    await page.screenshot({ path: 'test-results/auth-mobile-account.png', fullPage: true });
    expect(errors).toEqual([]);
});
