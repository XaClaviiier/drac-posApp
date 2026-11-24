<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('auth_events', function (Blueprint $table): void {
            $table->bigIncrements('id');
            $table->uuid('actor_user_id')->charset('ascii')->collation('ascii_bin')->nullable();
            $table->string('event', 50);
            $table->char('identifier_hash', 64)->charset('ascii')->collation('ascii_bin')->nullable();
            $table->ipAddress('ip_address')->nullable();
            $table->dateTime('occurred_at', 6)->index();
            $table->foreign('actor_user_id')->references('id')->on('users')->restrictOnDelete()->restrictOnUpdate();
            $table->index(['actor_user_id', 'occurred_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('auth_events');
    }
};
