param(
  [string]$TextFile,
  [string]$OutDir,
  [string]$Voice = "Microsoft Irina Desktop",
  [int]$Rate = -2,
  [int]$Pitch = -3
)
Add-Type -AssemblyName System.Speech
$lines = Get-Content -LiteralPath $TextFile -Encoding UTF8 | Where-Object { $_.Trim().Length -gt 0 }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$n = 0
foreach ($line in $lines) {
  $n++
  $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $synth.SelectVoice($Voice)
  $synth.Rate = $Rate
  $out = Join-Path $OutDir ("line{0:d2}.wav" -f $n)
  $synth.SetOutputToWaveFile($out)
  $ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ru-RU'><prosody rate='-4%' pitch='$Pitch%'>$line</prosody></speak>"
  $synth.SpeakSsml($ssml)
  $synth.Dispose()
}
Write-Output ("готово: " + $n + " дорожек в " + $OutDir)
