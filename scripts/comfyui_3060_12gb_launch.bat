@echo off
title ComfyUI — Perfil Optimizado RTX 3060 12GB + Ryzen 9 5900X + 32GB RAM

REM Ajusta esta ruta a tu instalacion local de ComfyUI en Windows 11
set COMFY_DIR=C:\AI\ComfyUI
set PYTHON_EXE=%COMFY_DIR%\venv\Scripts\python.exe

REM Evita fragmentacion VRAM en PyTorch Windows (Ampere 12GB)
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
set CUDA_MODULE_LOADING=LAZY

echo ============================================================================
echo  Iniciando ComfyUI (Perfil 3060 12GB / 32GB RAM / Windows 11)
echo  Tip: Cierra Premiere, After Effects, Blender y pestanas pesadas antes.
echo ============================================================================

if not exist "%PYTHON_EXE%" (
    echo [AVISO] No se encontro %PYTHON_EXE% - ajusta COMFY_DIR arriba.
    pause
    exit /b 1
)

REM Verificacion rapida de VRAM libre
nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv,noheader

cd /d "%COMFY_DIR%"

REM --normalvram funciona mejor que --lowvram cuando usas GGUF Q4/Q5 + BlockSwap;
REM agrega --lowvram solo si encadenas TextEncoder + DiT + Upscaler en una sola corrida.
"%PYTHON_EXE%" main.py --listen 127.0.0.1 --port 8188 --normalvram --preview-method auto --fast

pause
