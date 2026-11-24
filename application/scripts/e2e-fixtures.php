<?php

declare(strict_types=1);

use App\Models\User;
use Illuminate\Contracts\Console\Kernel;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

require dirname(__DIR__).'/vendor/autoload.php';
$app = require dirname(__DIR__).'/bootstrap/app.php';
$app->loadEnvironmentFrom('.env.e2e');
$app->make(Kernel::class)->bootstrap();

if (config('database.default') !== 'mysql'
    || config('database.connections.mysql.database') !== 'pos_auth_e2e'
    || config('database.connections.mysql.host') !== '127.0.0.1'
    || (int) config('database.connections.mysql.port') !== 13306) {
    fwrite(STDERR, "Fixture browser hanya diizinkan pada database pos_auth_e2e lokal.\n");
    exit(1);
}
$path = dirname(__DIR__, 2).'/.local/auth-e2e-accounts.json';
$action = $argv[1] ?? '';
if ($action === 'setup') {
    if (is_file($path)) {
        fwrite(STDERR, "Fixture lama masih ada. Jalankan cleanup sebelum membuat yang baru.\n");
        exit(1);
    }
    $app->make(Kernel::class)->call('db:seed', ['--force' => true]);
    $accounts = [];
    DB::transaction(function () use (&$accounts): void {
        foreach (['Owner', 'Teknisi', 'Kasir'] as $role) {
            $username = 'e2e_'.strtolower($role).'_'.bin2hex(random_bytes(5));
            $password = bin2hex(random_bytes(24));
            $user = User::query()->create(['username' => $username, 'name' => $role.' Uji Browser', 'password' => Hash::make($password), 'is_active' => true]);
            $user->assignRole($role);
            $accounts[strtolower($role)] = ['id' => $user->id, 'username' => $username, 'password' => $password];
        }
    });
    file_put_contents($path, json_encode($accounts, JSON_THROW_ON_ERROR), LOCK_EX);
    @chmod($path, 0600);
    echo "Tiga akun browser sementara dibuat; tidak ada kredensial yang dicetak.\n";
} elseif ($action === 'cleanup') {
    if (!is_file($path)) {
        exit(0);
    }
    $accounts = json_decode(file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
    DB::transaction(function () use ($accounts): void {
        foreach ($accounts as $account) {
            if (!str_starts_with($account['username'], 'e2e_')) {
                throw new RuntimeException('Identitas fixture tidak sesuai.');
            }
            $user = User::query()->whereKey($account['id'])->where('username', $account['username'])->first();
            if ($user) {
                // Keep actor references and audit events; these are test-only inactive accounts.
                $user->forceFill(['is_active' => false, 'password' => Hash::make(bin2hex(random_bytes(32)))])->save();
            }
        }
    });
    unlink($path);
    echo "Akun uji dinonaktifkan dan kredensial sementara dihapus.\n";
} else {
    fwrite(STDERR, "Gunakan setup atau cleanup.\n");
    exit(1);
}
