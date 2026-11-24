<?php

use App\Models\User;
use Database\Seeders\RolePermissionSeeder;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

beforeEach(function (): void {
    $this->seed(RolePermissionSeeder::class);
});

function authAccount(string $role = 'Kasir', array $attributes = []): User
{
    $user = User::factory()->create(['password' => 'Correct-Horse-42!', ...$attributes]);
    $user->assignRole($role);

    return $user;
}

it('logs in each role using database identity and a UUID', function (string $role, string $workspace): void {
    $user = authAccount($role);
    $this->withSession(['previous' => 'value']);
    $oldSession = session()->getId();

    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])
        ->assertOk()
        ->assertExactJson([
            'user' => ['id' => $user->id, 'username' => $user->username, 'name' => $user->name, 'roles' => [$role]],
            'workspace' => '/workspace/'.$workspace,
        ]);

    expect(Str::isUuid($user->id))->toBeTrue()
        ->and(session()->getId())->not->toBe($oldSession);
    $this->assertAuthenticatedAs($user, 'web');
    $this->getJson('/api/session')->assertOk()->assertJsonPath('user.id', $user->id);
    $this->assertDatabaseHas('model_has_roles', ['model_id' => $user->id, 'model_type' => User::class]);
    $this->assertDatabaseHas('auth_events', ['event' => 'login.succeeded', 'actor_user_id' => $user->id]);
})->with([
    ['Owner', 'owner'],
    ['Teknisi', 'teknisi'],
    ['Kasir', 'kasir'],
]);

it('normalizes username without modifying the password', function (): void {
    $user = authAccount(attributes: ['username' => 'kasir.satu', 'password' => '  Exact Password 42!  ']);

    $this->postJson('/login', ['username' => '  KASIR.SATU  ', 'password' => '  Exact Password 42!  '])
        ->assertOk()->assertJsonPath('user.id', $user->id);
});

it('uses one generic error for wrong unknown inactive and unassigned accounts', function (string $kind): void {
    $username = 'unknown.account';
    $password = 'Correct-Horse-42!';

    if ($kind !== 'unknown') {
        $user = $kind === 'unassigned'
            ? User::factory()->create(['password' => $password])
            : authAccount(attributes: ['is_active' => $kind !== 'inactive']);
        $username = $user->username;
    }

    $this->postJson('/login', [
        'username' => $username,
        'password' => $kind === 'wrong' ? 'Definitely-Wrong!' : $password,
    ])->assertUnprocessable()->assertExactJson(['message' => 'Username atau password salah.']);

    $this->assertGuest('web');
    $event = DB::table('auth_events')->where('event', 'login.failed')->first();
    expect($event)->not->toBeNull()
        ->and($event->identifier_hash)->toHaveLength(64)
        ->and(json_encode($event))->not->toContain($username, $password, 'Definitely-Wrong!');
    if ($kind === 'unknown') {
        expect($event->actor_user_id)->toBeNull();
    }
})->with(['wrong', 'unknown', 'inactive', 'unassigned']);

it('validates login fields without authenticating', function (array $payload, string $field): void {
    $this->postJson('/login', $payload)->assertUnprocessable()->assertJsonValidationErrors($field);
    $this->assertGuest('web');
})->with([
    [[], 'username'],
    [['username' => [], 'password' => 'anything'], 'username'],
    [['username' => 'valid', 'password' => []], 'password'],
    [['username' => str_repeat('a', 101), 'password' => 'anything'], 'username'],
]);

it('rejects role and permission injection without assigning anything', function (string $field, mixed $value): void {
    $user = authAccount();

    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!', $field => $value])
        ->assertUnprocessable()->assertJsonValidationErrors($field);

    expect($user->fresh()->getRoleNames()->all())->toBe(['Kasir']);
    $this->assertGuest('web');
})->with([
    ['role', 'Owner'],
    ['roles', ['Owner']],
    ['permissions', ['workspace.owner']],
    ['is_active', true],
]);

it('returns JSON 401 for guest sessions and workspace requests even without Accept', function (): void {
    $this->get('/api/session')->assertUnauthorized()->assertJsonPath('message', 'Unauthenticated.');
    $this->get('/api/workspaces/owner')->assertUnauthorized();
    $this->postJson('/logout')->assertUnauthorized();
});

it('never accepts bearer tokens as SPA authentication', function (): void {
    $this->withHeader('Authorization', 'Bearer 123|not-a-session')->getJson('/api/session')->assertUnauthorized();
});

it('invalidates existing sessions after deactivation or role removal', function (string $change): void {
    $user = authAccount();
    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])->assertOk();

    if ($change === 'inactive') {
        $user->update(['is_active' => false]);
    } else {
        $user->syncRoles([]);
    }

    $this->getJson('/api/session')->assertUnauthorized();
    $this->assertGuest('web');
    $this->assertDatabaseHas('auth_events', ['event' => 'session.denied', 'actor_user_id' => $user->id]);
})->with(['inactive', 'unassigned']);

it('authorizes each workspace on the server', function (string $role, string $workspace, int $status): void {
    $user = authAccount($role);
    $this->actingAs($user, 'web')->getJson('/api/workspaces/'.$workspace)->assertStatus($status);
})->with([
    ['Owner', 'owner', 200], ['Owner', 'teknisi', 200], ['Owner', 'kasir', 200],
    ['Teknisi', 'owner', 403], ['Teknisi', 'teknisi', 200], ['Teknisi', 'kasir', 403],
    ['Kasir', 'owner', 403], ['Kasir', 'teknisi', 403], ['Kasir', 'kasir', 200],
]);

it('does not promote a cashier with a direct owner permission', function (): void {
    $user = authAccount();
    $user->givePermissionTo('workspace.owner');

    $this->actingAs($user, 'web')->getJson('/api/workspaces/owner')->assertForbidden();
});

it('chooses the highest assigned role and returns only explicit account fields', function (): void {
    $user = authAccount('Kasir');
    $user->assignRole('Teknisi', 'Owner');

    $response = $this->actingAs($user, 'web')->getJson('/api/workspaces/owner')->assertOk();
    expect(array_keys($response->json('user')))->toBe(['id', 'username', 'name', 'roles'])
        ->and($response->json('workspace'))->toBe('/workspace/owner')
        ->and($response->json('permissions'))->toBe(['workspace.kasir', 'workspace.owner', 'workspace.teknisi']);
    $this->getJson('/api/session')->assertJsonPath('workspace', '/workspace/owner');
    expect($response->getContent())->not->toContain('password', 'remember_token', 'is_active', 'version');
});

it('logs out and invalidates session data and CSRF token', function (): void {
    $user = authAccount();
    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])->assertOk();
    session()->put('private_marker', 'remove-me');
    $oldId = session()->getId();
    $oldToken = session()->token();

    $this->postJson('/logout')->assertNoContent()->assertSessionMissing('private_marker');
    expect(session()->getId())->not->toBe($oldId)
        ->and(session()->token())->not->toBe($oldToken);
    $this->assertGuest('web');
    Auth::forgetGuards();
    $this->getJson('/api/session')->assertUnauthorized();
    $this->assertDatabaseHas('auth_events', ['event' => 'logout', 'actor_user_id' => $user->id]);
});

it('persists UUID sessions and deletes the old server session on logout', function (): void {
    config(['session.driver' => 'database']);
    $user = authAccount();
    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])->assertOk();
    $sessionId = session()->getId();
    $cookieName = config('session.cookie');

    $this->assertDatabaseHas('sessions', ['id' => $sessionId, 'user_id' => $user->id]);
    Auth::forgetGuards();
    $this->withCredentials()->withCookie($cookieName, $sessionId)->postJson('/logout')->assertNoContent();
    $this->assertDatabaseMissing('sessions', ['id' => $sessionId]);
    Auth::forgetGuards();
    $this->withCookie($cookieName, $sessionId)->getJson('/api/session')->assertUnauthorized();
});

it('limits normalized username and IP and permits retry after the window', function (): void {
    $user = authAccount(attributes: ['username' => 'rate.limited']);

    for ($attempt = 0; $attempt < 5; $attempt++) {
        $this->postJson('/login', ['username' => $attempt % 2 ? ' RATE.LIMITED ' : 'rate.limited', 'password' => 'wrong'])
            ->assertUnprocessable();
    }

    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])
        ->assertTooManyRequests()->assertHeader('Retry-After')->assertExactJson(['message' => 'Username atau password salah.']);
    $this->assertDatabaseHas('auth_events', ['event' => 'login.throttled']);
    $this->travel(61)->seconds();
    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])->assertOk();
});

it('does not throttle another username with the same IP', function (): void {
    for ($attempt = 0; $attempt < 5; $attempt++) {
        $this->postJson('/login', ['username' => 'blocked.account', 'password' => 'wrong'])->assertUnprocessable();
    }
    $user = authAccount();
    $this->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])->assertOk();
});

it('keeps unknown API routes as JSON instead of the SPA shell', function (): void {
    $this->get('/api/unknown')->assertNotFound()->assertHeader('Content-Type', 'application/json');
    $this->postJson('/register', ['username' => 'new'])->assertNotFound();
});

it('seeds roles and permissions without creating default accounts', function (): void {
    $this->seed();
    $this->seed();

    $this->assertDatabaseCount('users', 0);
    $this->assertDatabaseCount('roles', 3);
    $this->assertDatabaseCount('permissions', 3);
});

it('uses restrictive historical audit foreign keys', function (): void {
    $user = authAccount();
    $this->actingAs($user, 'web')->postJson('/logout')->assertNoContent();

    expect(fn () => $user->delete())->toThrow(\Illuminate\Database\QueryException::class);
    $this->assertDatabaseHas('users', ['id' => $user->id]);
});

it('keeps the throttle separate for different IP addresses', function (): void {
    $user = authAccount(attributes: ['username' => 'shared.username']);

    for ($attempt = 0; $attempt < 5; $attempt++) {
        $this->postJson('/login', ['username' => $user->username, 'password' => 'wrong'])->assertUnprocessable();
    }

    $this->withServerVariables(['REMOTE_ADDR' => '127.0.0.2'])
        ->postJson('/login', ['username' => $user->username, 'password' => 'Correct-Horse-42!'])
        ->assertOk();
});
