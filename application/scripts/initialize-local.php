<?php

declare(strict_types=1);

// This bootstrap creates only a fresh, project-owned local instance. Never reuse
// it against an existing datadir or deploy it as a production installer.
$project = dirname(__DIR__, 2);
$app = dirname(__DIR__);
$local = $project.'/.local';
$base = $local.'/mysql-8.4.13-winx64';
$data = $local.'/mysql-data';
$port = 13306;
$exe = $base.'/bin/mysqld.exe';

if (PHP_SAPI !== 'cli' || PHP_OS_FAMILY !== 'Windows') {
    fwrite(STDERR, "Bootstrap ini khusus CLI Windows lokal.\n");
    exit(1);
}
if (!is_file($exe) || is_dir($data) || is_file($app.'/.env')) {
    fwrite(STDERR, "Perlu ZIP MySQL 8.4.13 yang telah diekstrak; datadir dan .env harus belum ada. Tidak ada file lama yang ditimpa.\n");
    exit(1);
}
$socket = @stream_socket_client('tcp://127.0.0.1:'.$port, $error, $message, 0.5);
if ($socket !== false) {
    fclose($socket);
    fwrite(STDERR, "Port lokal yang dipilih sudah digunakan. Tidak menghubungi instance tersebut.\n");
    exit(1);
}

$rootPassword = bin2hex(random_bytes(32));
$appPassword = bin2hex(random_bytes(32));
$process = null;
$initFile = $local.'/mysql-first-start.sql';
$clientFile = $local.'/mysql-root.cnf';
$log = $local.'/mysql-bootstrap.log';
$files = $local.'/mysql-files';
if (!is_dir($files)) {
    mkdir($files, 0700, true);
}
$run = static function (array $command) use ($log): void {
    $child = proc_open($command, [0 => ['file', 'NUL', 'r'], 1 => ['file', $log, 'a'], 2 => ['file', $log, 'a']], $pipes, null, null, ['bypass_shell' => true]);
    if (!is_resource($child) || proc_close($child) !== 0) {
        throw new RuntimeException('Operasi MySQL gagal. Periksa log lokal tanpa membagikan isinya sebagai kredensial.');
    }
};
try {
    $run([$exe, '--no-defaults', '--initialize-insecure', '--basedir='.$base, '--datadir='.$data]);
    $ini = "[mysqld]\nbasedir=\"".str_replace('\\', '/', $base)."\"\ndatadir=\"".str_replace('\\', '/', $data)."\"\nbind-address=127.0.0.1\nport=$port\nmysqlx=OFF\nskip-name-resolve=ON\nlocal-infile=OFF\nsecure-file-priv=\"".str_replace('\\', '/', $files)."\"\ncharacter-set-server=utf8mb4\ncollation-server=utf8mb4_unicode_ci\ndefault-time-zone=+00:00\ninnodb-buffer-pool-size=64M\n";
    file_put_contents($local.'/mysql.ini', $ini, LOCK_EX);
    $sql = "ALTER USER 'root'@'localhost' IDENTIFIED BY '$rootPassword';\n";
    $sql .= "CREATE USER 'pos_app'@'127.0.0.1' IDENTIFIED BY '$appPassword';\n";
    foreach (['pos_development', 'pos_auth_testing', 'pos_auth_e2e'] as $database) {
        $sql .= "CREATE DATABASE `$database` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n";
        $sql .= "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES ON `$database`.* TO 'pos_app'@'127.0.0.1';\n";
    }
    file_put_contents($initFile, $sql, LOCK_EX);
    file_put_contents($clientFile, "[client]\nuser=root\npassword=$rootPassword\nhost=127.0.0.1\nport=$port\nprotocol=TCP\n", LOCK_EX);
    @chmod($initFile, 0600);
    @chmod($clientFile, 0600);
    $process = proc_open([$exe, '--defaults-file='.$local.'/mysql.ini', '--init-file='.$initFile, '--console'], [0 => ['file', 'NUL', 'r'], 1 => ['file', $log, 'a'], 2 => ['file', $log, 'a']], $pipes, null, null, ['bypass_shell' => true]);
    if (!is_resource($process)) {
        throw new RuntimeException('Tidak dapat menjalankan MySQL privat.');
    }
    $ready = false;
    for ($attempt = 0; $attempt < 120; $attempt++) {
        $status = proc_get_status($process);
        if (!$status['running']) {
            break;
        }
        try {
            $pdo = new PDO('mysql:host=127.0.0.1;port='.$port.';dbname=pos_development', 'pos_app', $appPassword, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
            $version = $pdo->query('SELECT VERSION()')->fetchColumn();
            if (!str_starts_with((string) $version, '8.4.13')) {
                throw new RuntimeException('Versi server tidak sesuai paket yang diinisialisasi.');
            }
            $ready = true;
            break;
        } catch (PDOException) {
            usleep(250000);
        }
    }
    if (!$ready) {
        throw new RuntimeException('MySQL privat belum siap. File konfigurasi lama tidak diubah.');
    }
    unset($pdo);
    $template = file_get_contents($app.'/.env.example');
    foreach (['.env' => ['local', 'pos_development', 'file'], '.env.testing' => ['testing', 'pos_auth_testing', 'array'], '.env.e2e' => ['local', 'pos_auth_e2e', 'file']] as $filename => [$environment, $database, $sessionDriver]) {
        $values = ['APP_ENV' => $environment, 'APP_KEY' => 'base64:'.base64_encode(random_bytes(32)), 'DB_DATABASE' => $database, 'DB_PASSWORD' => $appPassword, 'SESSION_DRIVER' => $sessionDriver, 'CACHE_PREFIX' => $database];
        $content = $template;
        foreach ($values as $key => $value) {
            $content = preg_replace('/^'.preg_quote($key, '/').'=.*$/m', $key.'='.$value, $content);
        }
        if ($filename !== '.env') {
            $content = preg_replace('/^BCRYPT_ROUNDS=.*$/m', 'BCRYPT_ROUNDS=4', $content);
        }
        file_put_contents($app.'/'.$filename, $content, LOCK_EX);
        @chmod($app.'/'.$filename, 0600);
    }
    echo "MySQL $version lokal berhasil disiapkan pada 127.0.0.1:$port.\n";
    echo "Database development, testing dan e2e terpisah. Kredensial hanya berada pada file lokal yang diabaikan Git.\n";
} catch (Throwable $exception) {
    fwrite(STDERR, $exception instanceof RuntimeException ? $exception->getMessage()."\n" : "Bootstrap gagal; periksa log lokal. Rahasia tidak dicetak.\n");
    $failed = true;
} finally {
    if (is_resource($process)) {
        try {
            $run([$base.'/bin/mysqladmin.exe', '--defaults-file='.$clientFile, 'shutdown']);
        } catch (Throwable) {
            proc_terminate($process);
        }
        proc_close($process);
        // MySQL's Windows launcher may exit before its worker releases InnoDB.
        // Wait for the owned server PID file, not just the launcher or TCP state.
        $deadline = microtime(true) + 30;
        while (glob($data.'/*.pid') !== [] && microtime(true) < $deadline) {
            usleep(100000);
            clearstatcache();
        }
        if (glob($data.'/*.pid') !== []) {
            fwrite(STDERR, "MySQL bootstrap belum selesai berhenti. Jangan menjalankan instance kedua pada datadir ini.\n");
            $failed = true;
        }
    }
    if (is_file($initFile)) {
        unlink($initFile);
    }
}
exit(isset($failed) ? 1 : 0);
