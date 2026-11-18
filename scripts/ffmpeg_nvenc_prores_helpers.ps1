<#
.SYNOPSIS
  Helpers PowerShell + FFmpeg para VFX, ProRes 4444 (Straight Alpha), NVENC RTX 3060 y Proxies.
  Importar en tu sesión: . .\scripts\ffmpeg_nvenc_prores_helpers.ps1
#>

function ConvertTo-ProRes4444Alpha {
    param(
        [Parameter(Mandatory=$true)][string]$InputPattern, # Ej: ".\frames\frame_%05d.png"
        [Parameter(Mandatory=$true)][string]$OutputMov,    # Ej: ".\out\roto_alpha.mov"
        [int]$Fps = 24
    )
    # -pix_fmt yuva444p10le conserva 10-bit + canal alpha Straight limpio para AE/Premiere/Resolve/EffectCraft
    ffmpeg -y -framerate $Fps -i $InputPattern `
        -c:v prores_ks -profile:v 4444 -vendor apl0 -bits_per_mb 8000 `
        -pix_fmt yuva444p10le -alpha_bits 16 `
        $OutputMov
}

function Combine-RgbAndMatteToProRes4444 {
    param(
        [Parameter(Mandatory=$true)][string]$RgbVideo,
        [Parameter(Mandatory=$true)][string]$MatteVideo,
        [Parameter(Mandatory=$true)][string]$OutputMov
    )
    # Une un video RGB y un Luma Matte (MatAnyone 2 / SAM3 / RMBG) en un solo MOV ProRes 4444
    ffmpeg -y -i $RgbVideo -i $MatteVideo `
        -filter_complex "[0:v]format=rgba[fg];[1:v]format=gray[a];[fg][a]alphamerge,format=yuva444p10le[out]" `
        -map "[out]" -map 0:a? -c:v prores_ks -profile:v 4444 -c:a pcm_s24le `
        $OutputMov
}

function Export-NvencHevcMaster {
    param(
        [Parameter(Mandatory=$true)][string]$InputFile,
        [Parameter(Mandatory=$true)][string]$OutputMp4,
        [int]$Cq = 18
    )
    # Usa chip NVENC de RTX 3060 para archivos ligeros de alta calidad (Windows 11 / Premiere compatible)
    ffmpeg -y -i $InputFile `
        -c:v hevc_nvenc -preset p6 -tune hq -rc vbr -cq $Cq -b:v 0 -pix_fmt p010le `
        -tag:v hvc1 -c:a aac -b:a 320k -movflags +faststart `
        $OutputMp4
}

function New-EditProxy720p {
    param(
        [Parameter(Mandatory=$true)][string]$InputFile,
        [Parameter(Mandatory=$true)][string]$OutputProxy
    )
    ffmpeg -y -i $InputFile `
        -vf "scale=-2:720" -c:v h264_nvenc -preset p4 -cq 22 -g 15 `
        -c:a aac -b:a 192k `
        $OutputProxy
}
