<#
.SYNOPSIS
  Auditoría e Instalador Guiado del Módulo C (TouchDesigner + Blender + Antigravity + MoCap)
  Perfil objetivo: Windows 11 · RTX 3060 12 GB · Ryzen 9 5900X · 32 GB RAM
.DESCRIPTION
  Verifica prerequisitos locales (TouchDesigner 2025.33230+, Blender 4.5/5.x, uv, agy),
  muestra la configuración exacta de Antigravity (~/.gemini/config/mcp_config.json)
  y opcionalmente registra los servidores MCP si se pasa -ApplyAntigravityMCP.
#>
param(
    [switch]$ApplyAntigravityMCP
)

Write-Host "=== Módulo C · Auditoría TouchDesigner + Blender + MoCap (Windows 11) ===" -ForegroundColor Cyan

# 1. Verificar CLI de Antigravity (agy), uv, git y Python
$cmds = @("agy", "uv", "uvx", "python", "git", "ffmpeg")
foreach ($c in $cmds) {
    $found = Get-Command $c -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "[OK] $c -> $($found.Source)" -ForegroundColor Green
    } else {
        Write-Host "[FALTA] $c" -ForegroundColor Yellow
        if ($c -in @("uv", "uvx")) {
            Write-Host "   -> Instala uv ejecutando: winget install --id=astral-sh.uv -e" -ForegroundColor DarkGray
        }
    }
}

# 2. Detectar instalaciones de TouchDesigner y Blender en rutas estándar de Windows
Write-Host "`n=== 2. Aplicaciones Nativas (TouchDesigner & Blender) ===" -ForegroundColor Cyan
$tdPaths = Get-ChildItem "C:\Program Files\Derivative\TouchDesigner*" -ErrorAction SilentlyContinue
if ($tdPaths) {
    foreach ($td in $tdPaths) { Write-Host "[OK] TouchDesigner: $($td.FullName)" -ForegroundColor Green }
    Write-Host "   Recuerda usar build 2025.33230+ para TDMCP oficial y Point File In POP (3DGS)." -ForegroundColor DarkGray
} else {
    Write-Host "[AVISO] No se detectó TouchDesigner en C:\Program Files\Derivative\" -ForegroundColor Yellow
}

$blenderPaths = Get-ChildItem "C:\Program Files\Blender Foundation\Blender*" -ErrorAction SilentlyContinue
if ($blenderPaths) {
    foreach ($bl in $blenderPaths) { Write-Host "[OK] Blender: $($bl.FullName)" -ForegroundColor Green }
} else {
    Write-Host "[AVISO] No se detectó Blender en C:\Program Files\Blender Foundation\" -ForegroundColor Yellow
}

# 3. Revisar estado de Antigravity mcp_config.json y skills locales
Write-Host "`n=== 3. Configuración Antigravity MCP & Skills ===" -ForegroundColor Cyan
$agyConfig = Join-Path $env:USERPROFILE ".gemini\config\mcp_config.json"
$agySkills = Join-Path $env:USERPROFILE ".gemini\config\skills"
Write-Host "Archivo MCP global Antigravity: $agyConfig"
Write-Host "Carpeta User Skills Antigravity: $agySkills"

if (Test-Path $agySkills) {
    $tdSkills = Get-ChildItem $agySkills -Directory -Filter "td-*" -ErrorAction SilentlyContinue
    Write-Host "Skills td-* instaladas a nivel usuario: $($tdSkills.Count)" -ForegroundColor Cyan
}

if ($ApplyAntigravityMCP) {
    if (Get-Command "agy" -ErrorAction SilentlyContinue) {
        Write-Host "`nRegistrando TDMCP (127.0.0.1:13316/mcp) en Antigravity..." -ForegroundColor Cyan
        & agy mcp add touchdesigner http://127.0.0.1:13316/mcp
    } else {
        Write-Warning "No se encontró 'agy' en PATH. Copia manualmente mcps\antigravity_td_blender_mcp.json hacia $agyConfig"
    }

    if (Get-Command "uvx" -ErrorAction SilentlyContinue) {
        Write-Host "Lanzando asistente oficial mcp-for-blender setup..." -ForegroundColor Cyan
        & uvx mcp-for-blender setup
    } else {
        Write-Warning "Instala 'uv' primero: winget install --id=astral-sh.uv -e"
    }
} else {
    Write-Host "`n[Modo Solo Lectura] Para registrar MCPs automáticamente ejecuta:" -ForegroundColor DarkCyan
    Write-Host "  .\scripts\setup_module_c_win11.ps1 -ApplyAntigravityMCP" -ForegroundColor White
}

Write-Host "`n=== 4. Checklist de Add-ons / Componentes Manuales en Apps ===" -ForegroundColor Cyan
Write-Host "1) TouchDesigner: Arrastra TDMCP.tox -> Active=On -> Install For=Antigravity -> Install Skills."
Write-Host "2) TouchDesigner (Git/TDXN): Opcionalmente usa dylanroscover/Embody (puerto 9870)."
Write-Host "3) Blender Spout2 Sender: Instala maybites/TextureSharing v9.1.1+ en Edit > Preferences > Add-ons."
Write-Host "4) Blender 3DGS: Instala Kiri-Innovation/3dgs-render-blender-addon para .ply compartidos."
Write-Host "5) Markerless MoCap: Clona toyxyz/toyxyz_RGBMocap y corre install.cmd (GVHMR usa solo ~4.2 GB VRAM)."
