<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('users', function (Blueprint $table) {
            $table->uuid('id')->charset('ascii')->collation('ascii_bin')->primary();
            $table->string('username', 100)->unique();
            $table->string('name', 200);
            $table->string('password');
            $table->rememberToken();
            $table->boolean('is_active')->default(true);
            $table->unsignedBigInteger('version')->default(1);
            $table->dateTime('created_at', 6);
            $table->dateTime('updated_at', 6);
        });

        DB::statement('ALTER TABLE users ADD CONSTRAINT ck_users_username CHECK (CHAR_LENGTH(TRIM(username)) > 0), ADD CONSTRAINT ck_users_name CHECK (CHAR_LENGTH(TRIM(name)) > 0), ADD CONSTRAINT ck_users_active CHECK (is_active IN (0, 1)), ADD CONSTRAINT ck_users_version CHECK (version > 0)');

        Schema::create('sessions', function (Blueprint $table) {
            $table->string('id')->primary();
            $table->uuid('user_id')->charset('ascii')->collation('ascii_bin')->nullable()->index();
            $table->string('ip_address', 45)->nullable();
            $table->text('user_agent')->nullable();
            $table->longText('payload');
            $table->integer('last_activity')->index();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('sessions');
        Schema::dropIfExists('users');
    }
};
