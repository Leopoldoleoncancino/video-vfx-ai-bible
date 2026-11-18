#!/usr/bin/env python3
"""Orquestador secuencial de pipeline VFX para GPUs de 12 GB VRAM (RTX 3060 + 32 GB RAM).

Principio clave: nunca mantener simultáneamente múltiples modelos de difusión/matting en VRAM.
Cada paso invoca un subproceso aislado que libera CUDA al terminar:
  Paso 1: Extracción de secuencia de frames PNG o detección de escenas (FFmpeg)
  Paso 2: Matting / Segmentación externa (hook customizable hacia MatAnyone 2 / SAM 3 / ComfyUI API)
  Paso 3: Empaquetado final sin halos a ProRes 4444 (`yuva444p10le`) para Adobe / EffectCraft / Resolve.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], dry_run: bool = False) -> None:
    print("[CMD]", " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg no está instalado en PATH.", file=sys.stderr)
        sys.exit(1)


def build_pipeline(args: argparse.Namespace) -> None:
    work = Path(args.work_dir).resolve()
    frames_dir = work / "01_frames"
    matte_dir = work / "02_matte"
    out_dir = work / "03_master"
    for d in (frames_dir, matte_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Paso 1: Extraer secuencia PNG lossless + pista de audio PCM
    audio_wav = work / "audio.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(args.input_video),
            "-vf",
            f"fps={args.fps}",
            str(frames_dir / "frame_%05d.png"),
        ],
        dry_run=args.dry_run,
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(args.input_video),
            "-vn",
            "-c:a",
            "pcm_s24le",
            str(audio_wav),
        ],
        dry_run=args.dry_run,
    )

    # Paso 2: Hook para MatAnyone 2 / SAM 3 (ejemplo declarativo en manifest JSON para evitar colisión VRAM)
    manifest = {
        "input_frames": str(frames_dir),
        "output_matte": str(matte_dir),
        "recommended_3060_12gb_chunk_size": args.chunk_size,
        "step_command_example": (
            f"python inference_matanyone2.py --input {frames_dir} "
            f"--output {matte_dir} --max_size 1080"
        ),
    }
    manifest_path = work / "matting_job.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[INFO] Manifest de matting guardado en {manifest_path}")

    # Paso 3: Si ya se proporcionó un video/secuencia matte o se ejecutó el paso 2, empaquetar ProRes 4444
    if args.matte_video:
        out_mov = out_dir / f"{Path(args.input_video).stem}_prores4444_alpha.mov"
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(args.input_video),
                "-i",
                str(args.matte_video),
                "-filter_complex",
                "[0:v]format=rgba[fg];[1:v]format=gray[a];[fg][a]alphamerge,format=yuva444p10le[out]",
                "-map",
                "[out]",
                "-map",
                "0:a?",
                "-c:v",
                "prores_ks",
                "-profile:v",
                "4444",
                "-c:a",
                "pcm_s24le",
                str(out_mov),
            ],
            dry_run=args.dry_run,
        )
        print(f"[OK] Master ProRes 4444 con Alpha listo: {out_mov}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Orquestador secuencial VFX para RTX 3060 12GB")
    p.add_argument("--input-video", required=True, help="Clip de entrada MP4/MOV")
    p.add_argument("--work-dir", default="./vfx_job", help="Carpeta de trabajo")
    p.add_argument("--matte-video", default="", help="Opcional: video/secuencia Luma Matte ya generado")
    p.add_argument("--fps", type=int, default=24, help="Framerate objetivo")
    p.add_argument("--chunk-size", type=int, default=64, help="Tamaño de lote para no saturar 12GB VRAM / 32GB RAM")
    p.add_argument("--dry-run", action="store_true", help="Muestra comandos sin ejecutar FFmpeg")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.dry_run:
        check_ffmpeg()
    build_pipeline(args)
