<!DOCTYPE html>
<html lang="id">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="color-scheme" content="light dark">
        <meta name="robots" content="noindex, nofollow">
        <title>Ruang kerja bengkel</title>
        <script>
            (() => {
                let theme;
                try { theme = localStorage.getItem('pos-theme'); } catch {}
                const dark = theme === 'dark' || (theme !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                document.documentElement.dataset.theme = dark ? 'dark' : 'light';
            })();
        </script>
        @viteReactRefresh
        @vite('resources/js/app.tsx')
    </head>
    <body>
        <div id="app"></div>
        <noscript>Aktifkan JavaScript untuk masuk ke ruang kerja bengkel.</noscript>
    </body>
</html>
