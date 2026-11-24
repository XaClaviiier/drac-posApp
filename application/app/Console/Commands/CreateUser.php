<?php

namespace App\Console\Commands;

use App\Auth\WorkspaceAccess;
use App\Models\User;
use App\Services\AuthAudit;
use Database\Seeders\RolePermissionSeeder;
use Illuminate\Console\Command;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

class CreateUser extends Command
{
    protected $signature = 'pos:create-user';

    protected $description = 'Create an active account interactively with a role and a hidden, confirmed password';

    public function handle(AuthAudit $audit): int
    {
        if (! $this->input->isInteractive()) {
            $this->error('Jalankan pos:create-user di terminal interaktif. Password tidak boleh diberikan melalui argumen.');

            return self::FAILURE;
        }

        $username = Str::lower(trim((string) $this->ask('Username')));
        $name = trim((string) $this->ask('Nama'));
        $role = $this->choice('Peran', array_values(WorkspaceAccess::ROLES));
        $password = $this->secret('Password (minimal 12 karakter)', false);
        $confirmation = $this->secret('Konfirmasi password', false);
        $validator = Validator::make([
            'username' => $username,
            'name' => $name,
            'role' => $role,
            'password' => $password,
            'password_confirmation' => $confirmation,
        ], [
            'username' => ['required', 'string', 'max:100', 'regex:/\A[a-z0-9][a-z0-9._-]*\z/', Rule::unique('users', 'username')],
            'name' => ['required', 'string', 'max:200'],
            'role' => ['required', Rule::in(array_values(WorkspaceAccess::ROLES))],
            'password' => [
                'required', 'string', 'min:12', 'confirmed',
                function (string $attribute, mixed $value, \Closure $fail): void {
                    if (is_string($value) && strlen($value) > 72) {
                        $fail('Password maksimal 72 byte agar tidak terpotong oleh bcrypt.');
                    }
                },
            ],
        ]);

        if ($validator->fails()) {
            foreach ($validator->errors()->all() as $error) {
                $this->error($error);
            }

            return self::FAILURE;
        }

        try {
            $user = DB::transaction(function () use ($username, $name, $password, $role, $audit): User {
                (new RolePermissionSeeder)->run();
                $user = User::create([
                    'username' => $username,
                    'name' => $name,
                    'password' => $password,
                    'is_active' => true,
                ]);
                $user->assignRole($role);
                $audit->record('account.created', username: $username);

                return $user;
            });
        } catch (UniqueConstraintViolationException) {
            $this->error('Username sudah digunakan. Jalankan ulang dengan username lain.');

            return self::FAILURE;
        }

        $this->info('Akun dibuat: '.$user->id.' ('.$role.').');

        return self::SUCCESS;
    }
}
