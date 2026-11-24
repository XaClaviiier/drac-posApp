<?php

use App\Models\User;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

it('creates an active UUID account and its role in one operation', function (): void {
    $this->artisan('pos:create-user')
        ->expectsQuestion('Username', '  ADMIN.SATU  ')
        ->expectsQuestion('Nama', ' Pemilik Bengkel ')
        ->expectsChoice('Peran', 'Owner', ['Owner', 'Teknisi', 'Kasir'])
        ->expectsQuestion('Password (minimal 12 karakter)', 'Long-Unique-Password!')
        ->expectsQuestion('Konfirmasi password', 'Long-Unique-Password!')
        ->assertSuccessful();

    $user = User::where('username', 'admin.satu')->firstOrFail();
    expect(Str::isUuid($user->id))->toBeTrue()
        ->and($user->name)->toBe('Pemilik Bengkel')
        ->and($user->is_active)->toBeTrue()
        ->and($user->version)->toBe(1)
        ->and(Hash::check('Long-Unique-Password!', $user->password))->toBeTrue()
        ->and($user->getRoleNames()->all())->toBe(['Owner']);
    $this->assertDatabaseCount('users', 1);
    $this->assertDatabaseCount('roles', 3);
    $this->assertDatabaseHas('auth_events', ['event' => 'account.created', 'actor_user_id' => null]);
    expect(json_encode(DB::table('auth_events')->get()))->not->toContain('admin.satu', 'Long-Unique-Password!');
});

it('rejects invalid account fields without partial accounts roles or audit rows', function (string $username, string $name, string $password, string $confirmation): void {
    $this->artisan('pos:create-user')
        ->expectsQuestion('Username', $username)
        ->expectsQuestion('Nama', $name)
        ->expectsChoice('Peran', 'Kasir', ['Owner', 'Teknisi', 'Kasir'])
        ->expectsQuestion('Password (minimal 12 karakter)', $password)
        ->expectsQuestion('Konfirmasi password', $confirmation)
        ->assertFailed();

    $this->assertDatabaseCount('users', 0);
    $this->assertDatabaseCount('roles', 0);
    $this->assertDatabaseCount('auth_events', 0);
})->with([
    ['', 'Name', 'Long-Unique-Password!', 'Long-Unique-Password!'],
    ['invalid name', 'Name', 'Long-Unique-Password!', 'Long-Unique-Password!'],
    ['valid.name', '  ', 'Long-Unique-Password!', 'Long-Unique-Password!'],
    ['valid.name', 'Name', 'short', 'short'],
    ['valid.name', 'Name', 'Long-Unique-Password!', 'Different-Password!'],
    ['valid.name', 'Name', str_repeat('a', 73), str_repeat('a', 73)],
    ['valid.name', 'Name', str_repeat('é', 37), str_repeat('é', 37)],
]);

it('refuses duplicate usernames without changing existing accounts', function (): void {
    $existing = User::factory()->create(['username' => 'already.used']);

    $this->artisan('pos:create-user')
        ->expectsQuestion('Username', 'ALREADY.USED')
        ->expectsQuestion('Nama', 'Another Person')
        ->expectsChoice('Peran', 'Owner', ['Owner', 'Teknisi', 'Kasir'])
        ->expectsQuestion('Password (minimal 12 karakter)', 'Long-Unique-Password!')
        ->expectsQuestion('Konfirmasi password', 'Long-Unique-Password!')
        ->assertFailed();

    $this->assertDatabaseCount('users', 1);
    $this->assertDatabaseCount('roles', 0);
    expect($existing->fresh()->getRoleNames()->all())->toBe([]);
});

it('refuses unattended account creation with no password arguments', function (): void {
    $this->artisan('pos:create-user', ['--no-interaction' => true])->assertFailed();
    $this->assertDatabaseCount('users', 0);
});
