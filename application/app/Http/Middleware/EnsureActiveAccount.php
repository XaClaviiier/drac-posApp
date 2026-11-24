<?php

namespace App\Http\Middleware;

use App\Auth\WorkspaceAccess;
use App\Services\AuthAudit;
use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Symfony\Component\HttpFoundation\Response;

class EnsureActiveAccount
{
    public function __construct(private readonly AuthAudit $audit) {}

    public function handle(Request $request, Closure $next): Response
    {
        $user = $request->user()?->fresh();

        if ($user === null || ! $user->is_active || WorkspaceAccess::defaultWorkspace($user) === null) {
            $this->audit->record('session.denied', $user, $request);
            Auth::guard('web')->logout();
            $request->session()->invalidate();
            $request->session()->regenerateToken();

            return response()->json(['message' => 'Unauthenticated.'], 401);
        }

        Auth::guard('web')->setUser($user);
        Auth::guard('sanctum')->setUser($user);

        return $next($request);
    }
}
