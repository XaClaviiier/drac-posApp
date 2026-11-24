<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    public function createApplication()
    {
        $app = parent::createApplication();
        $connection = $app['config']->get('database.default');
        $settings = $app['config']->get('database.connections.'.$connection, []);

        // Check before RefreshDatabase can run any destructive migration command.
        if (! $app->environment('testing')
            || $connection !== 'mysql'
            || ($settings['database'] ?? null) !== 'pos_auth_testing'
            || ! in_array($settings['host'] ?? null, ['127.0.0.1', 'localhost'], true)
            || ! empty($settings['url'])) {
            throw new \RuntimeException('AUTH-01 tests require the isolated local MySQL pos_auth_testing database without DB_URL.');
        }

        return $app;
    }
}
