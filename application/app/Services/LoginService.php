<?php

namespace App\Services;

use App\Auth\WorkspaceAccess;
use App\Models\User;
use Illuminate\Http\Exceptions\HttpResponseException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\RateLimiter;

final class LoginService
{
    public const INVALID_CREDENTIALS = 'Username atau password salah.';

    public function __construct(private readonly AuthAudit $audit) {}

    public function login(Request $request, string $username, #[\SensitiveParameter] string $password): User
    {
        $key = 'login:'.$this->audit->identifier($username.'|'.$request->ip());

        if (RateLimiter::tooManyAttempts($key, 5)) {
            $this->audit->record('login.throttled', request: $request, username: $username);
            throw new HttpResponseException(response()->json([
                'message' => self::INVALID_CREDENTIALS,
            ], 429, ['Retry-After' => (string) RateLimiter::availableIn($key)]));
        }

        RateLimiter::hit($key, 60);
        $guard = Auth::guard('web');
        $valid = $guard->attemptWhen(
            ['username' => $username, 'password' => $password],
            fn (User $user): bool => $user->is_active && WorkspaceAccess::defaultWorkspace($user) !== null,
            false,
        );

        if (! $valid) {
            $this->audit->record('login.failed', $guard->getLastAttempted(), $request, $username);
            throw new HttpResponseException(response()->json(['message' => self::INVALID_CREDENTIALS], 422));
        }

        $request->session()->regenerate();
        RateLimiter::clear($key);
        /** @var User $user */
        $user = $guard->user();
        $this->audit->record('login.succeeded', $user, $request);

        return $user;
    }
}
