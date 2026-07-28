param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,

  [Parameter(Mandatory = $true)]
  [string]$OutputPath,

  [string]$LanguageTag = 'zh-Hans-CN',

  [double]$Scale = 1.0,

  [double]$XOffset = 0.0,

  [double]$YOffset = 0.0
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = (
  [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object {
      $_.Name -eq 'AsTask' -and
      $_.GetParameters().Count -eq 1 -and
      $_.IsGenericMethod
    }
)[0]

function Await-WinRT {
  param(
    [Parameter(Mandatory = $true)]
    $Operation,

    [Parameter(Mandatory = $true)]
    [Type]$ResultType
  )

  $task = $asTaskGeneric.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
  $task.Wait()
  return $task.Result
}

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory) {
  New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}

$file = Await-WinRT `
  ([Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]::GetFileFromPathAsync($resolvedInput)) `
  ([Windows.Storage.StorageFile])
$stream = Await-WinRT `
  ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) `
  ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await-WinRT `
  ([Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]::CreateAsync($stream)) `
  ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await-WinRT `
  ($decoder.GetSoftwareBitmapAsync()) `
  ([Windows.Graphics.Imaging.SoftwareBitmap])

$language = New-Object `
  ([Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]) `
  $LanguageTag
$engine = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]::TryCreateFromLanguage($language)
if ($null -eq $engine) {
  throw "Windows OCR language is unavailable: $LanguageTag"
}

$result = Await-WinRT `
  ($engine.RecognizeAsync($bitmap)) `
  ([Windows.Media.Ocr.OcrResult])

$lines = foreach ($line in $result.Lines) {
  $words = foreach ($word in $line.Words) {
    $rect = $word.BoundingRect
    [ordered]@{
      text = $word.Text
      x = [Math]::Round(($rect.X / $Scale) + $XOffset, 2)
      y = [Math]::Round(($rect.Y / $Scale) + $YOffset, 2)
      width = [Math]::Round($rect.Width / $Scale, 2)
      height = [Math]::Round($rect.Height / $Scale, 2)
    }
  }

  [ordered]@{
    text = $line.Text
    words = @($words)
  }
}

$payload = [ordered]@{
  source = [System.IO.Path]::GetFileName($resolvedInput)
  language = $LanguageTag
  scale = $Scale
  xOffset = $XOffset
  yOffset = $YOffset
  text = $result.Text
  lines = @($lines)
}

$payload |
  ConvertTo-Json -Depth 8 |
  Set-Content -LiteralPath $OutputPath -Encoding UTF8

[ordered]@{
  source = $payload.source
  characters = $result.Text.Length
  lines = $result.Lines.Count
  words = (@($result.Lines | ForEach-Object { $_.Words })).Count
  output = (Resolve-Path -LiteralPath $OutputPath).Path
} | ConvertTo-Json -Compress
