param(
  [string]$TextFile,
  [string]$OutDir,
  [string]$Match = "Pavel"
)
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]

$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

$lines = Get-Content -LiteralPath $TextFile -Encoding UTF8 | Where-Object { $_.Trim().Length -gt 0 }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$synth = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::new()
$voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.DisplayName -like "*$Match*" -or $_.Id -like "*$Match*" } | Select-Object -First 1
if (-not $voice) {
  Write-Output ("голос не найден: " + $Match)
  [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | ForEach-Object { Write-Output ("  " + $_.DisplayName + " | " + $_.Id) }
  exit 1
}
$synth.Voice = $voice
Write-Output ("голос: " + $voice.DisplayName)

$n = 0
foreach ($line in $lines) {
  $n++
  $op = $synth.SynthesizeTextToStreamAsync($line)
  $task = $asTask.MakeGenericMethod([Windows.Media.SpeechSynthesis.SpeechSynthesisStream]).Invoke($null, @($op))
  $task.Wait()
  $stream = $task.Result
  $reader = [Windows.Storage.Streams.DataReader]::new($stream.GetInputStreamAt(0))
  $size = [uint32]$stream.Size
  $loadOp = $reader.LoadAsync($size)
  $loadTask = $asTask.MakeGenericMethod([uint32]).Invoke($null, @($loadOp))
  $loadTask.Wait() | Out-Null
  $bytes = New-Object byte[] $size
  $reader.ReadBytes($bytes)
  $out = Join-Path $OutDir ("oc{0:d2}.wav" -f $n)
  [System.IO.File]::WriteAllBytes($out, $bytes)
  $reader.Dispose()
  $stream.Dispose()
}
Write-Output ("готово: " + $n + " дорожек в " + $OutDir)
