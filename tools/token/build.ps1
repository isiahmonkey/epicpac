# Token incremental build: only re-converts textures and re-compiles models whose source changed.
param([string]$GMOD = 'C:\Program Files (x86)\Steam\steamapps\common\GarrysMod')
$ErrorActionPreference = 'Continue'
$KIT  = $PSScriptRoot
$GAME = Join-Path $GMOD 'garrysmod'
$SRC  = Join-Path $GAME 'materialsrc\models\player\token'
$MD   = Join-Path $GAME 'materials\models\player\token'
$MO   = Join-Path $GAME 'models\player\token'
$VTEX = Join-Path $GMOD 'bin\vtex.exe'
$MDLC = Join-Path $GMOD 'bin\studiomdl.exe'
if (!(Test-Path $MDLC)) { Write-Host "Can't find studiomdl at $MDLC - edit GMOD in build.bat" -ForegroundColor Red; exit 1 }
$sw = [Diagnostics.Stopwatch]::StartNew()

# 0. unpack any kit / patch zips Claude dropped in
Get-ChildItem $KIT -Filter 'token_build*.zip' | ForEach-Object {
  Write-Host "Unpacking $($_.Name)"; Expand-Archive -Force -LiteralPath $_.FullName -DestinationPath $KIT; Remove-Item $_.FullName }

# hash cache
$cacheFile = Join-Path $KIT '.cache\hashes.json'
New-Item -ItemType Directory -Force (Split-Path $cacheFile) | Out-Null
$cache = @{}
if (Test-Path $cacheFile) { (Get-Content $cacheFile -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $cache[$_.Name] = $_.Value } }
function H([string[]]$files) { ($files | ForEach-Object { if (Test-Path $_) { (Get-FileHash $_ -Algorithm MD5).Hash } else { 'missing' } }) -join '' }
function RunParallel($jobs, [int]$max) {   # jobs: list of @{exe; args; name}
  $running = @()
  foreach ($j in $jobs) {
    while (@($running | Where-Object { -not $_.HasExited }).Count -ge $max) { Start-Sleep -Milliseconds 200 }
    $running += Start-Process -FilePath $j.exe -ArgumentList $j.args -NoNewWindow -PassThru -RedirectStandardOutput $j.log -RedirectStandardError "$($j.log).err"
  }
  $running | ForEach-Object { $_.WaitForExit() }
}
$cpu = [Math]::Max(2, [Environment]::ProcessorCount - 1)

# 1. textures
New-Item -ItemType Directory -Force $SRC, $MD, $MO, (Join-Path $KIT 'logs') | Out-Null
$tex = @()
foreach ($t in Get-ChildItem (Join-Path $KIT 'materialsrc') -Filter *.tga) {
  $txt = [IO.Path]::ChangeExtension($t.FullName, '.txt'); $key = 'tex:' + $t.BaseName; $h = H @($t.FullName, $txt)
  $vtf = Join-Path $MD ($t.BaseName + '.vtf')
  if ($cache[$key] -ne $h -or !(Test-Path $vtf)) {
    Copy-Item $t.FullName, $txt $SRC -Force
    $tex += @{ exe = $VTEX; args = @('-nopause','-quiet','-game',"`"$GAME`"","`"$(Join-Path $SRC $t.Name)`""); log = (Join-Path $KIT "logs\vtex_$($t.BaseName).txt"); key = $key; h = $h; out = $vtf }
  }
}
Write-Host "[1/3] Textures: $($tex.Count) changed"
RunParallel $tex $cpu
foreach ($j in $tex) { if (Test-Path $j.out) { $cache[$j.key] = $j.h } else { Write-Host "  vtex FAILED: $($j.out)" -ForegroundColor Red } }
Copy-Item (Join-Path $KIT 'materials\*.vmt') $MD -Force

# 2. models
$mdl = @()
foreach ($q in Get-ChildItem (Join-Path $KIT 'modelsrc') -Filter *.qc) {
  $refs = Select-String -Path $q.FullName -Pattern '"([^"]+\.smd)"' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { Join-Path (Join-Path $KIT 'modelsrc') $_.Groups[1].Value } | Sort-Object -Unique
  $key = 'mdl:' + $q.BaseName; $h = H (@($q.FullName) + $refs); $out = Join-Path $MO ($q.BaseName + '.mdl')
  if ($cache[$key] -ne $h -or !(Test-Path $out)) {
    if (Test-Path $out) { Remove-Item $out }
    $mdl += @{ exe = $MDLC; args = @('-nop4','-game',"`"$GAME`"","`"$($q.FullName)`""); log = (Join-Path $KIT "logs\studiomdl_$($q.BaseName).txt"); key = $key; h = $h; out = $out }
  }
}
Write-Host "[2/3] Models: $($mdl.Count) changed $(($mdl | ForEach-Object { Split-Path $_.out -Leaf }) -join ', ')"
RunParallel $mdl 4
foreach ($j in $mdl) {
  $bad = Select-String -Path $j.log -Pattern 'ERROR','too many' -SimpleMatch
  if ((Test-Path $j.out) -and !$bad) { $cache[$j.key] = $j.h } else { Write-Host "  studiomdl problem, see $($j.log)" -ForegroundColor Red; $bad | ForEach-Object { Write-Host "   $($_.Line)" } }
}
$cache | ConvertTo-Json | Set-Content $cacheFile

# 3. one PAC3 zip per model (token_base + each outfit)
Write-Host "[3/3] Packing PAC3 zips"
$out = Join-Path $KIT 'pac3'
foreach ($p in Get-ChildItem (Join-Path $KIT 'plans') -Filter *.json) {
  $plan = Get-Content $p.FullName -Raw | ConvertFrom-Json; $m = $plan.model; $d = Join-Path $out $m
  if (Test-Path $d) { Remove-Item $d -Recurse -Force }; New-Item -ItemType Directory -Force $d | Out-Null
  foreach ($e in 'mdl','vvd','dx90.vtx','phy') { $f = Join-Path $MO "$m.$e"; if (Test-Path $f) { Copy-Item $f $d } }
  foreach ($mt in $plan.materials) { foreach ($f in "$mt.vmt","$mt.vtf","${mt}_n.vtf") { $g = Join-Path $MD $f; if (Test-Path $g) { Copy-Item $g $d } } }
  $zip = Join-Path $KIT "${m}_pac3.zip"; if (Test-Path $zip) { Remove-Item $zip }
  Compress-Archive -Path (Join-Path $d '*') -DestinationPath $zip
  Write-Host ("  {0}  {1:N1} MB" -f (Split-Path $zip -Leaf), ((Get-Item $zip).Length / 1MB))
}
Write-Host ("Done in {0:N0} s - tell Claude when finished." -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green
