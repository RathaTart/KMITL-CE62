# Resumable downloader for the large CUDA wheels.
#
# `pip install` cannot resume a partial download: when the connection to
# download.pytorch.org drops mid-transfer (which it does on this link), pip
# restarts the 2.4 GB torch wheel from zero. This fetches the wheels with HTTP
# Range requests and retries until each file is byte-complete, so progress
# survives a dropped connection. pip is then pointed at the local files.

param(
    [string]$OutDir = "$PSScriptRoot\..\wheels",
    [int]$MaxAttempts = 200
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$urls = @(
    "https://download.pytorch.org/whl/cu121/torch-2.4.1%2Bcu121-cp312-cp312-win_amd64.whl",
    "https://download.pytorch.org/whl/cu121/torchvision-0.19.1%2Bcu121-cp312-cp312-win_amd64.whl"
)

function Get-RemoteSize([string]$url) {
    $req = [System.Net.HttpWebRequest]::Create($url)
    $req.Method = "HEAD"
    $req.Timeout = 60000
    $resp = $req.GetResponse()
    try { return $resp.ContentLength } finally { $resp.Close() }
}

foreach ($url in $urls) {
    $name = [System.Uri]::UnescapeDataString(($url -split '/')[-1])
    $dest = Join-Path $OutDir $name
    $total = Get-RemoteSize $url
    Write-Output "[wheel] $name  total $([math]::Round($total/1MB)) MB"

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $have = if (Test-Path $dest) { (Get-Item $dest).Length } else { 0 }
        if ($have -ge $total) { break }

        try {
            $req = [System.Net.HttpWebRequest]::Create($url)
            $req.Timeout = 60000
            $req.ReadWriteTimeout = 120000
            $req.AddRange([long]$have)
            $resp = $req.GetResponse()
            $in = $resp.GetResponseStream()
            $out = [System.IO.File]::Open($dest, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
            $buf = New-Object byte[] (4 * 1024 * 1024)
            try {
                while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) { $out.Write($buf, 0, $n) }
            } finally {
                $out.Close(); $in.Close(); $resp.Close()
            }
        } catch {
            $now = if (Test-Path $dest) { (Get-Item $dest).Length } else { 0 }
            Write-Output ("[wheel] {0} attempt {1}: {2} ({3:N0}/{4:N0} MB)" -f `
                $name, $attempt, $_.Exception.Message, ($now / 1MB), ($total / 1MB))
            Start-Sleep -Seconds 3
        }
    }

    $final = (Get-Item $dest).Length
    if ($final -ne $total) { throw "$name incomplete: $final of $total bytes" }
    Write-Output "[wheel] $name COMPLETE"
}

Write-Output "ALL WHEELS COMPLETE"
