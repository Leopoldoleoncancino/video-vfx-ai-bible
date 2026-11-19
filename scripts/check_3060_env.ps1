<#
.SYNOPSIS
  Auditoría rápida de estación de trabajo Windows 11 para Video IA + VFX
  Perfil objetivo: NVIDIA RTX 3060 12 GB + AMD Ryzen 9 5900X + 32 GB RAM
#>
param(
    [string]$ComfyDir = "",
    [string]$PythonExe = "python"
)

Write-Host "=== 1. GPU & VRAM (nvidia-smi) ===" -ForegroundColor Cyan
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free,memory.used --format=csv,noheader
} else {
    Write-Warning "nvidia-smi no encontrado en PATH."
}

Write-Host "`n=== 2. RAM Física & Pagefile NVMe (Crítico para 32 GB + modelos 14B) ===" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$totalRamGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$freeRamGB  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
Write-Host "RAM Total: $totalRamGB GB | RAM Libre actual: $freeRamGB GB"
if ($freeRamGB -lt 20) {
    Write-Warning "Menos de 20 GB RAM libre: cierra Premiere/After Effects/Chrome antes de cargar Wan 2.2 14B o LTX-2.5."
}

$pf = Get-CimInstance Win32_PageFileUsage
if ($pf) {
    foreach ($p in $pf) {
        Write-Host "Pagefile [$($p.Name)]: Asignado $($p.AllocatedBaseSize) MB | Pico $($p.PeakUsage) MB"
        if ($p.AllocatedBaseSize -lt 32768) {
            Write-Warning "Recomendación 32GB RAM: subir Pagefile en tu NVMe a 32768-65536 MB para evitar MemoryError en cargas sharded."
        }
    }
} else {
    Write-Host "Pagefile administrado por el sistema (verifica tener >=32 GB disponibles en NVMe)."
}

Write-Host "`n=== 3. Runtimes & Herramientas CLI ===" -ForegroundColor Cyan
$tools = @("python", "uv", "git", "node", "npm", "cargo", "ffmpeg", "ffprobe", "gh")
foreach ($t in $tools) {
    $cmd = Get-Command $t -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "[OK] $t -> $($cmd.Source)" -ForegroundColor Green
    } else {
        Write-Host "[FALTA] $t" -ForegroundColor Yellow
    }
}

Write-Host "`n=== 4. Adobe CEP PlayerDebugMode (para Premiere/AE MCP locales) ===" -ForegroundColor Cyan
foreach ($ver in @("CSXS.11", "CSXS.12")) {
    $regPath = "HKCU:\Software\Adobe\$ver"
    if (Test-Path $regPath) {
        $val = (Get-ItemProperty -Path $regPath -Name "PlayerDebugMode" -ErrorAction SilentlyContinue).PlayerDebugMode
        Write-Host "$ver PlayerDebugMode = $val"
    } else {
        Write-Host "$ver no registrado aún (para activar: New-Item '$regPath' -Force; New-ItemProperty ... PlayerDebugMode='1')"
    }
}

Write-Host "`n=== 5. Procesos pesados consumiendo GPU/RAM ===" -ForegroundColor Cyan
Get-Process -Name "Adobe Premiere Pro","AfterFX","blender","TouchDesigner","Resolve","chrome" -ErrorAction SilentlyContinue |
    Select-Object ProcessName, @{Name="RAM_GB";Expression={[math]::Round($_.WorkingSet64/1GB,2)}} |
    Format-Table -AutoSize

Write-Host "`n=== 6. PyTorch Ampere (sm_86) & Librerías VFX (Módulo A) ===" -ForegroundColor Cyan
if (Get-Command $PythonExe -ErrorAction SilentlyContinue) {
    $pyProbe = @'
import importlib.util, json
res = {}
for mod in ["torch", "triton", "sageattention", "cv2", "pymatting", "OpenEXR", "PyOpenColorIO", "PIL"]:
    res[mod] = importlib.util.find_spec(mod) is not None
if res.get("torch"):
    import torch
    res["cuda"] = torch.cuda.is_available()
    if torch.cuda.is_available():
        cap = torch.cuda.get_device_capability(0)
        res["sm"] = f"sm_{cap[0]}{cap[1]}"
        res["fp8_fast_warning"] = (cap[0] * 10 + cap[1]) < 89
print(json.dumps(res))
'@
    try {
        $outJson = & $PythonExe -c $pyProbe 2>$null
        if ($outJson) {
            Write-Host "Python [$PythonExe]: $outJson"
            if ($outJson -match '"fp8_fast_warning": true') {
                Write-Host "[NOTA sm_86] RTX 3060 Ampere detectada: usa GGUF Q3_K_M/Q4_K_S o BF16+sageattn; evita fp8_fast y torch.compile en e4m3fn." -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Warning "No se pudo consultar entorno Python [$PythonExe]."
    }
}

Write-Host "`n=== 7. Auditoría Opcional ComfyUI custom_nodes (MatAnyone2 max_mem_frames) ===" -ForegroundColor Cyan
$candidateComfy = if ($ComfyDir) { @($ComfyDir) } else { @("C:\AI\ComfyUI", "C:\ComfyUI", "$env:USERPROFILE\ComfyUI") }
$foundComfy = $false
foreach ($cdir in $candidateComfy) {
    if (Test-Path (Join-Path $cdir "custom_nodes")) {
        $foundComfy = $true
        Write-Host "[OK] ComfyUI detectado en: $cdir" -ForegroundColor Green
        $cfgFiles = Get-ChildItem -Path (Join-Path $cdir "custom_nodes") -Filter "config.py" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "matanyone" }
        foreach ($cf in $cfgFiles) {
            $txt = Get-Content $cf.FullName -Raw -ErrorAction SilentlyContinue
            if ($txt -match '"max_mem_frames"\s*:\s*(\d+)') {
                $mmf = [int]$Matches[1]
                if ($mmf -gt 5) {
                    Write-Warning "$($cf.FullName) tiene max_mem_frames=$mmf (recomendado <=5 para secuencias largas en 12 GB VRAM)."
                } else {
                    Write-Host "[OK] $($cf.Name) max_mem_frames=$mmf" -ForegroundColor Green
                }
            }
        }
    }
}
if (-not $foundComfy) {
    Write-Host "Ruta ComfyUI no detectada automáticamente (puedes pasar -ComfyDir 'D:\ComfyUI')."
}
