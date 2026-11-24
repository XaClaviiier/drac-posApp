param(
    [ValidateSet('start', 'stop')]
    [string]$Action = 'start'
)
$ErrorActionPreference = 'Stop'
$project = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$local = Join-Path $project '.local'
$bin = Join-Path $local 'mysql-8.4.13-winx64/bin'
$config = Join-Path $local 'mysql.ini'
if (-not (Test-Path $config)) {
    throw 'Jalankan bootstrap database lokal terlebih dahulu. Tidak ada database existing yang diubah.'
}
if ($Action -eq 'start') {
    # Foreground process: stop it through the separate stop command for a clean shutdown.
    & (Join-Path $bin 'mysqld.exe') "--defaults-file=$config" --console
} else {
    & (Join-Path $bin 'mysqladmin.exe') "--defaults-file=$(Join-Path $local 'mysql-root.cnf')" shutdown
}
exit $LASTEXITCODE
