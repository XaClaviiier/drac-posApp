<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\WorkspaceController;
use Illuminate\Support\Facades\Route;

Route::redirect('/', '/login');
Route::view('/login', 'app')->name('login');
Route::view('/workspace/{workspace}', 'app')->whereIn('workspace', ['owner', 'teknisi', 'kasir']);

Route::post('/login', [AuthController::class, 'login']);

// Require a web session before Sanctum, so bearer tokens are never accepted.
Route::middleware(['auth:web', 'auth:sanctum', 'active.account'])->group(function (): void {
    Route::get('/api/session', [AuthController::class, 'session']);
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/api/workspaces/{workspace}', WorkspaceController::class)
        ->whereIn('workspace', ['owner', 'teknisi', 'kasir']);
});

Route::any('/api/{path?}', fn () => abort(404))->where('path', '.*');
