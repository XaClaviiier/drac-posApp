<?php

namespace Database\Seeders;

use App\Auth\WorkspaceAccess;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;
use Spatie\Permission\PermissionRegistrar;

class RolePermissionSeeder extends Seeder
{
    public function run(): void
    {
        $registrar = app(PermissionRegistrar::class);
        $registrar->forgetCachedPermissions();

        DB::transaction(function (): void {
            foreach (WorkspaceAccess::ROLES as $workspace => $name) {
                Permission::findOrCreate('workspace.'.$workspace, 'web');
                Role::findOrCreate($name, 'web');
            }

            Role::findByName('Owner', 'web')->givePermissionTo([
                'workspace.owner', 'workspace.teknisi', 'workspace.kasir',
            ]);
            Role::findByName('Teknisi', 'web')->givePermissionTo(['workspace.teknisi']);
            Role::findByName('Kasir', 'web')->givePermissionTo(['workspace.kasir']);
        });

        $registrar->forgetCachedPermissions();
    }
}
