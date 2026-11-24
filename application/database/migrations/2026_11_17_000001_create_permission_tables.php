<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        foreach (['permissions', 'roles'] as $name) {
            Schema::create($name, function (Blueprint $table): void {
                $table->bigIncrements('id');
                $table->string('name', 125);
                $table->string('guard_name', 125);
                $table->timestamps(6);
                $table->unique(['name', 'guard_name']);
            });
        }

        foreach (['permissions' => 'permission_id', 'roles' => 'role_id'] as $name => $key) {
            Schema::create('model_has_'.$name, function (Blueprint $table) use ($name, $key): void {
                $table->unsignedBigInteger($key);
                $table->string('model_type', 125);
                $table->uuid('model_id')->charset('ascii')->collation('ascii_bin');
                $table->index(['model_id', 'model_type']);
                $table->foreign($key)->references('id')->on($name)->restrictOnDelete()->restrictOnUpdate();
                $table->primary([$key, 'model_id', 'model_type']);
            });
        }

        Schema::create('role_has_permissions', function (Blueprint $table): void {
            $table->unsignedBigInteger('permission_id');
            $table->unsignedBigInteger('role_id');
            $table->foreign('permission_id')->references('id')->on('permissions')->restrictOnDelete()->restrictOnUpdate();
            $table->foreign('role_id')->references('id')->on('roles')->restrictOnDelete()->restrictOnUpdate();
            $table->primary(['permission_id', 'role_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('role_has_permissions');
        Schema::dropIfExists('model_has_roles');
        Schema::dropIfExists('model_has_permissions');
        Schema::dropIfExists('roles');
        Schema::dropIfExists('permissions');
    }
};
