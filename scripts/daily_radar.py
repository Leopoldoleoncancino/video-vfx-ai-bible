#!/usr/bin/env python3
"""Daily Radar para la Biblia de Video IA, VFX, Normales, Tracking 3D, OCIO/Audio/OBS, Animaciones JS, ArtCraft, Adobe, TouchDesigner y Blender.

Consulta las APIs públicas de GitHub y Hugging Face para detectar:
1. Nuevos repositorios / MCP servers / custom nodes / plugins en los 10 pilares.
2. Releases recientes y actividad en el watchlist estratégico (ArtCraft, Adobe MCPs, TD, Blender, Wan/LTX, MatAnyone, Normales, Tracking 3D, Audio IA, OBS, JS Video).
3. Modelos trending relevantes en Hugging Face (Video Gen, Matting, Depth, VSR, Audio/Lip-sync).

Uso local (Windows 11 / Linux):
  python scripts/daily_radar.py
Opcional:
  set GITHUB_TOKEN=ghp_...
  set LOOKBACK_DAYS=7
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
RADAR_MD_PATH = ROOT_DIR / "RADAR_DAILY.md"
RADAR_JSON_PATH = ROOT_DIR / "data" / "radar_latest.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "7"))
HAS_GH = shutil.which("gh") is not None

SEARCH_TOPICS: list[tuple[str, str, int]] = [
    ("IA Video Local & ComfyUI", "ComfyUI OR Wan2.2 OR LTX-2 OR HunyuanVideo OR Wan2GP OR comfy-mcp in:name,description,topics", 10),
    ("Rotoscopia, Matting, Depth & Inpainting", "matting OR rotoscoping OR MatAnyone OR SAM3 OR VideoMaMa OR DepthAnything in:name,description,topics", 5),
    ("Capa de Normales, Camera Tracking 3D & Geometría", "NormalCrafter OR StableNormal OR MoGe OR Relit-LiVE OR td-native-inference OR vggt OR co-tracker in:name,description,topics", 5),
    ("Color OCIO/ACES, Audio IA, Face VFX & OBS", "MMAudio OR whisperX OR LivePortrait OR obs-mcp OR OpenColorIO OR F5-TTS in:name,description,topics", 5),
    ("ArtCraft (Storytold Rust Suite)", "org:storytold", 0),
    ("Adobe Premiere / After Effects MCP & UXP", '"premiere pro mcp" OR "after effects mcp" OR premiere-pro-mcp OR after-effects-mcp OR "adobe uxp" in:name,description,topics', 3),
    ("TouchDesigner MCP, POPs & Real-Time", "touchdesigner OR StreamDiffusionTD OR TDMCP in:name,description,topics", 3),
    ("Blender, DaVinci Resolve, VFX & Open-Source Video", '"blender mcp" OR davinci-resolve-mcp OR OpenCut OR FlashVSR OR SeedVR2 in:name,description,topics', 5),
    ("Animaciones JS, WebGL & Video-as-Code", "remotion OR motion-canvas OR lottie OR theatrejs OR rive-wasm in:topics", 20),
]

WATCHLIST_REPOS: list[str] = [
    "storytold/artcraft",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "storytold/anicraft",
    "storytold/photocraft",
    "storytold/lightcraft",
    "storytold/texturecraft",
    "storytold/materialcraft",
    "storytold/soundcraft",
    "leancoderkavy/premiere-pro-mcp",
    "hetpatel-11/Adobe_Premiere_Pro_MCP",
    "Dakkshin/after-effects-mcp",
    "kumoproductions/mcp-aftereffects",
    "leonardogrig/opencutagent",
    "TouchDesigner/TDMCP",
    "dylanroscover/Embody",
    "8beeeaaat/touchdesigner-mcp",
    "Verbalize-public/td-mcp-rs",
    "cacheflowe/td-native-inference",
    "ahujasid/mcp-for-blender",
    "sideshowroberto/vfx-agent-toolkit",
    "samuelgursky/davinci-resolve-mcp",
    "Comfy-Org/comfy-mcp",
    "deepbeepmeep/WanGP",
    "Wan-Video/Wan2.2",
    "Lightricks/LTX-2",
    "Lightricks/LTX-Desktop",
    "Tencent-Hunyuan/HunyuanVideo-1.5",
    "pq-yang/MatAnyone2",
    "facebookresearch/sam3",
    "cvlab-kaist/VideoMaMa",
    "FudanCVL/EffectErase",
    "zhuxing0/Relit-LiVE",
    "Binyr/NormalCrafter",
    "zuanfilm/ComfyUI-VizClick-NormalCrafter",
    "Stable-X/StableNormal",
    "EnVision-Research/Lotus",
    "1038lab/ComfyUI-Lotus-2",
    "microsoft/MoGe",
    "microsoft/DAViD",
    "ByteDance-Seed/Depth-Anything-3",
    "facebookresearch/vggt",
    "yyfz/Pi3",
    "facebookresearch/co-tracker",
    "colmap/colmap",
    "AcademySoftwareFoundation/OpenColorIO",
    "hkchengrex/MMAudio",
    "m-bain/whisperX",
    "resemble-ai/chatterbox",
    "KlingAIResearch/LivePortrait",
    "Off-World-Live/obs-spout2-plugin",
    "royshil/obs-mcp",
    "OpenImagingLab/FlashVSR_Plus",
    "IceClear/SeedVR2",
    "OpenCut-app/OpenCut",
    "WyattBlue/auto-editor",
    "mifi/lossless-cut",
    "mrdoob/three.js",
    "remotion-dev/remotion",
    "greensock/GSAP",
    "juliangarnier/anime",
    "motion-canvas/motion-canvas",
    "rive-app/rive-wasm",
    "kijai/ComfyUI-WanVideoWrapper",
    "alibaba-damo-academy/Lumos-Custom",
    "FXTD-Studios/radiance",
    "BISAM20/ComfyUI-ACES-IO",
    "oumad/ComfyUI_Gear",
    "Code2Collapse/ComfyUI-CustomNodePacks",
    "fishfinger44/MatteDesk",
    "warmshao/WiLoR-mini",
    "numz/ComfyUI-SeedVR2_VideoUpscaler",
    "aharley/alltracker",
    "FuouM/ComfyUI-MatAnyone",
    "spiritform/comfy-matanyone2",
    "taichi-dev/taichi",
    "tum-pbs/PhiFlow",
    "kevinraymond/touchdesigner-effects",
    "Rikiya89/glsl_daily_practice",
    "torinmb/mediapipe-touchdesigner",
    "DarienBrito/TDXDepthCamMerger",
    "forkni/cuda-link",
    "Kosinkadink/ComfyUI-VideoHelperSuite",
    "kijai/ComfyUI-KJNodes",
    "city96/ComfyUI-GGUF",
]

HF_PIPELINES: list[tuple[str, str]] = [
    ("Text-to-Video", "text-to-video"),
    ("Image-to-Video", "image-to-video"),
    ("Video Classification / Segmentation / Depth", "depth-estimation"),
]


def http_get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    req_headers = {"User-Agent": "video-vfx-ai-bible-daily-radar/1.0"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gh_headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def gh_get_json(endpoint: str) -> Any:
    """Consulta GitHub API usando GITHUB_TOKEN si existe o vía `gh api` autenticado."""
    if GITHUB_TOKEN or not HAS_GH:
        return http_get_json(f"https://api.github.com/{endpoint}", gh_headers())
    res = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=25)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or f"gh api error for {endpoint}")
    return json.loads(res.stdout)


def fetch_topic_repos(query: str, since_date: str, min_stars: int = 5) -> list[dict[str, Any]]:
    # Si es org:storytold no filtramos por stars sino por actividad reciente
    if query.startswith("org:"):
        full_q = f"{query} pushed:>={since_date}"
    else:
        full_q = f"{query} pushed:>={since_date} stars:>={min_stars}"
    encoded = urllib.parse.quote(full_q)
    endpoint = f"search/repositories?q={encoded}&sort=updated&order=desc&per_page=8"
    try:
        data = gh_get_json(endpoint)
        items = data.get("items", [])
        return [
            {
                "full_name": it["full_name"],
                "url": it["html_url"],
                "stars": it.get("stargazers_count", 0),
                "pushed_at": (it.get("pushed_at") or "")[:10],
                "description": (it.get("description") or "").replace("\r", " ").replace("\n", " ").strip()[:140],
                "license": (it.get("license") or {}).get("spdx_id") or "Ver repo",
            }
            for it in items
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def _fetch_single_watchlist_repo(repo: str) -> dict[str, Any]:
    try:
        info = gh_get_json(f"repos/{repo}")
        rel_tag = "-"
        rel_date = "-"
        try:
            rel = gh_get_json(f"repos/{repo}/releases/latest")
            rel_tag = rel.get("tag_name") or "-"
            rel_date = (rel.get("published_at") or "")[:10] or "-"
        except urllib.error.HTTPError as he:
            if he.code != 404:
                rel_tag = f"err:{he.code}"
        except Exception as rexc:
            if "404" not in str(rexc):
                rel_tag = "sin-release"
        return {
            "full_name": info["full_name"],
            "url": info["html_url"],
            "stars": info.get("stargazers_count", 0),
            "pushed_at": (info.get("pushed_at") or "")[:10],
            "latest_release": rel_tag,
            "release_date": rel_date,
            "license": (info.get("license") or {}).get("spdx_id") or "Custom",
        }
    except Exception as exc:
        return {"full_name": repo, "url": f"https://github.com/{repo}", "error": str(exc)}


def fetch_watchlist_status() -> list[dict[str, Any]]:
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(_fetch_single_watchlist_repo, WATCHLIST_REPOS))
    rows.sort(key=lambda r: r.get("stars", -1), reverse=True)
    return rows


def fetch_hf_trending() -> dict[str, list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}
    for label, tag in HF_PIPELINES:
        url = f"https://huggingface.co/api/models?pipeline_tag={urllib.parse.quote(tag)}&sort=trendingScore&limit=6"
        try:
            data = http_get_json(url)
            results[label] = [
                {
                    "id": m.get("id"),
                    "url": f"https://huggingface.co/{m.get('id')}",
                    "downloads": m.get("downloads", 0),
                    "likes": m.get("likes", 0),
                }
                for m in data
            ]
        except Exception as exc:
            results[label] = [{"error": str(exc)}]
    return results


def render_markdown(
    generated_at: str,
    since_date: str,
    topics_data: list[tuple[str, list[dict[str, Any]]]],
    watchlist: list[dict[str, Any]],
    hf_data: dict[str, list[dict[str, Any]]],
) -> str:
    lines: list[str] = [
        "# Radar Diario Automatizado — Video IA, VFX, ArtCraft & Adobe",
        "",
        f"> Última actualización automática: **{generated_at} UTC** | Ventana de búsqueda: desde **{since_date}** (`LOOKBACK_DAYS={LOOKBACK_DAYS}`)",
        "",
        "Este archivo se regenera automáticamente cada día mediante [`.github/workflows/daily-radar.yml`](.github/workflows/daily-radar.yml) ejecutando [`scripts/daily_radar.py`](scripts/daily_radar.py), y también sirve como base de contexto para la automatización diaria `/automation` de Antigravity.",
        "",
        "---",
        "",
        "## 1. Watchlist Estratégico (Releases & Actividad Reciente)",
        "",
        "| Repositorio | Stars | Último Push | Último Release | Fecha Release | Licencia |",
        "|---|---:|---|---|---|---|",
    ]
    for r in watchlist:
        if "error" in r:
            lines.append(f"| [{r['full_name']}]({r['url']}) | - | Error consulta | - | - | - |")
        else:
            lines.append(
                f"| [{r['full_name']}]({r['url']}) | {r['stars']:,} | {r['pushed_at']} | `{r['latest_release']}` | {r['release_date']} | {r['license']} |"
            )

    lines.extend(["", "---", "", "## 2. Radar por Pilares en GitHub (Activos Recientemente)", ""])
    for topic_title, repos in topics_data:
        lines.append(f"### {topic_title}")
        lines.append("")
        if not repos:
            lines.append("_Sin resultados recientes en la ventana consultada._")
        elif "error" in repos[0]:
            lines.append(f"_Aviso de API: {repos[0]['error']}_")
        else:
            lines.append("| Proyecto | Stars | Último Push | Licencia | Descripción |")
            lines.append("|---|---:|---|---|---|")
            for rp in repos:
                desc = (rp["description"] or "-").replace("|", "\\|")
                lines.append(
                    f"| [{rp['full_name']}]({rp['url']}) | {rp['stars']:,} | {rp['pushed_at']} | {rp['license']} | {desc} |"
                )
        lines.append("")

    lines.extend(["---", "", "## 3. Modelos Trending en Hugging Face Hub", ""])
    for label, models in hf_data.items():
        lines.append(f"### {label}")
        lines.append("")
        if not models or "error" in models[0]:
            err = models[0].get("error", "Sin datos") if models else "Sin datos"
            lines.append(f"_Aviso de API Hugging Face: {err}_")
        else:
            lines.append("| Modelo HF | Likes | Descargas |")
            lines.append("|---|---:|---:|")
            for m in models:
                lines.append(f"| [{m['id']}]({m['url']}) | {m['likes']:,} | {m['downloads']:,} |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Recordatorio de Filtro RTX 3060 12GB + 32GB RAM",
        "",
        "Antes de adoptar cualquier modelo nuevo detectado arriba en tu PC local (Windows 11, 12 GB VRAM, 32 GB RAM):",
        "1. Verificar si existen pesos **GGUF (`Q4_K_M` / `Q5_K_M`)** o **FP8/INT8** compatibles con `ComfyUI-GGUF` o `Wan2GP (mmgp)`.",
        "2. Comprobar requisitos de **RAM de sistema**: en 32 GB RAM (~22-24 GB libres), evitar text-encoders BF16 >10 GB sin offloading o quantización.",
        "3. Revisar si ya existe un **MCP Server** o nodo oficial para **TouchDesigner / Blender / Premiere / After Effects / EffectCraft / FilmCraft**.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")

    topics_data: list[tuple[str, list[dict[str, Any]]]] = []
    for title, query, min_stars in SEARCH_TOPICS:
        topics_data.append((title, fetch_topic_repos(query, since, min_stars)))

    watchlist = fetch_watchlist_status()
    hf_data = fetch_hf_trending()

    RADAR_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": generated_at,
        "since_date": since,
        "lookback_days": LOOKBACK_DAYS,
        "watchlist": watchlist,
        "topics": {title: items for title, items in topics_data},
        "huggingface_trending": hf_data,
    }
    RADAR_JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md = render_markdown(generated_at, since, topics_data, watchlist, hf_data)
    RADAR_MD_PATH.write_text(md, encoding="utf-8")
    print(f"Radar actualizado correctamente en {RADAR_MD_PATH} y {RADAR_JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
