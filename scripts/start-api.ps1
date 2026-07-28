param(
  [Parameter(Mandatory = $true)]
  [string]$DbPassword,
  [string]$DbHost = '127.0.0.1',
  [int]$DbPort = 3306,
  [string]$DbUser = 'root',
  [string]$DbName = 'yuezi',
  [string]$ApiHost = '127.0.0.1',
  [int]$ApiPort = 3000,
  [string]$TokenSecret = 'qdf-local-development-token-secret',
  [string]$Python = 'C:\Users\39717\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:ERP_DB_HOST = $DbHost
$env:ERP_DB_PORT = [string]$DbPort
$env:ERP_DB_USER = $DbUser
$env:ERP_DB_PASSWORD = $DbPassword
$env:ERP_DB_NAME = $DbName
$env:ERP_API_HOST = $ApiHost
$env:ERP_API_PORT = [string]$ApiPort
$env:ERP_TOKEN_SECRET = $TokenSecret

Set-Location -LiteralPath $projectRoot
& $Python 'server\mvp_api.py' 'serve'
