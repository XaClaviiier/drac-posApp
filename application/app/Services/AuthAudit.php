<?php

namespace App\Services;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

final class AuthAudit
{
    public function identifier(string $username): string
    {
        return hash_hmac('sha256', $username, (string) config('app.key'));
    }

    public function record(string $event, ?User $actor = null, ?Request $request = null, ?string $username = null): void
    {
        DB::table('auth_events')->insert([
            'actor_user_id' => $actor?->id,
            'event' => $event,
            'identifier_hash' => $username === null ? null : $this->identifier($username),
            'ip_address' => $request?->ip(),
            'occurred_at' => now(),
        ]);
    }
}
