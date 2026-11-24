<?php

namespace App\Auth;

use App\Models\User;

final class WorkspaceAccess
{
    public const ROLES = [
        'owner' => 'Owner',
        'teknisi' => 'Teknisi',
        'kasir' => 'Kasir',
    ];

    public static function defaultWorkspace(User $user): ?string
    {
        foreach (self::ROLES as $workspace => $role) {
            if (self::allows($user, $workspace)) {
                return '/workspace/'.$workspace;
            }
        }

        return null;
    }

    public static function allows(User $user, string $workspace): bool
    {
        $role = self::ROLES[$workspace] ?? null;

        return $role !== null
            && $user->hasAnyRole(['Owner', $role])
            && $user->getAllPermissions()->contains('name', 'workspace.'.$workspace);
    }

    /** @return array{user: array{id: string, username: string, name: string, roles: list<string>}, workspace: string|null} */
    public static function session(User $user): array
    {
        return [
            'user' => [
                'id' => $user->id,
                'username' => $user->username,
                'name' => $user->name,
                'roles' => $user->getRoleNames()->sort()->values()->all(),
            ],
            'workspace' => self::defaultWorkspace($user),
        ];
    }
}
