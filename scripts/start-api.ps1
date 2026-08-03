param(
  [string]$DbHost = '127.0.0.1',
  [int]$DbPort = 3306,
  [string]$DbUser = 'yuezi_app',
  [string]$DbName = 'yuezi',
  [string]$ApiHost = '127.0.0.1',
  [int]$ApiPort = 3000,
  [ValidateSet('development', 'test', 'staging', 'production')]
  [string]$RuntimeEnv = 'development',
  [string]$Python = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $env:ERP_DB_PASSWORD) {
  throw 'Set ERP_DB_PASSWORD in the current session; never pass it as a CLI argument.'
}
if (-not $env:ERP_TOKEN_SECRET) {
  throw 'Set ERP_TOKEN_SECRET in the current session.'
}
if (-not $Python) {
  $Python = if ($env:ERP_PYTHON) { $env:ERP_PYTHON } else { 'python' }
}
$env:ERP_DB_HOST = $DbHost
$env:ERP_DB_PORT = [string]$DbPort
$env:ERP_DB_USER = $DbUser
$env:ERP_DB_NAME = $DbName
$env:ERP_API_HOST = $ApiHost
$env:ERP_API_PORT = [string]$ApiPort
$env:ERP_RUNTIME_ENV = $RuntimeEnv

Set-Location -LiteralPath $projectRoot
& $Python 'server\mvp_api.py' 'serve'
