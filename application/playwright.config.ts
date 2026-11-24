import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',
    fullyParallel: false,
    workers: 1,
    retries: 0,
    timeout: 30_000,
    use: {
        baseURL: 'http://127.0.0.1:8089',
        channel: 'chrome',
        viewport: { width: 1440, height: 960 },
        // Authentication fixtures are secrets; do not record request/cookie traces.
        trace: 'off',
        screenshot: 'off',
        video: 'off',
    },
    reporter: [['list'], ['json', { outputFile: 'test-results/auth-results.json' }]],
    webServer: {
        command: 'php artisan serve --host=127.0.0.1 --port=8089 --env=e2e --no-reload',
        url: 'http://127.0.0.1:8089/up',
        reuseExistingServer: false,
        timeout: 30_000,
    },
});
