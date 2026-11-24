import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import '@fontsource/poppins/latin-400.css';
import '@fontsource/poppins/latin-500.css';
import '@fontsource/poppins/latin-600.css';
import '../css/app.css';
import { createQueryClient } from './auth';
import { App } from './screens';

const element = document.getElementById('app');
if (!element) throw new Error('Application root is missing.');

createRoot(element).render(
    <StrictMode>
        <QueryClientProvider client={createQueryClient()}>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </QueryClientProvider>
    </StrictMode>,
);
