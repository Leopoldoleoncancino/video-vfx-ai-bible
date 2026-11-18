"""Blender -> TouchDesigner Live Camera & Frame OSC Bridge (Stdlib Only).

Uso en Blender 4.2 / 4.5 / 5.x (Windows 11):
1. Abre este script en Blender -> Scripting -> Open -> Run Script.
2. Abre el panel lateral de la Vista 3D (tecla N) -> pestaña "TD Bridge".
3. Ajusta IP (127.0.0.1) y Puerto UDP (9000), y pulsa "Start OSC Sync".
4. En TouchDesigner crea un "OSC In CHOP" escuchando en el puerto 9000.

No requiere dependencias externas (usa socket + struct nativos de Python).
"""

from __future__ import annotations

import math
import socket
import struct
from typing import Iterable

import bpy


bl_info = {
    "name": "TD Bridge OSC Sender",
    "author": "video-vfx-ai-bible",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N-Panel > TD Bridge",
    "description": "Transmite camara activa, frame y objeto objetivo hacia TouchDesigner OSC In CHOP sin dependencias pip",
    "category": "System",
}


def _pad4(data: bytes) -> bytes:
    rem = len(data) % 4
    return data + (b"\x00" * (4 - rem if rem else 0))


def _osc_str(text: str) -> bytes:
    return _pad4(text.encode("utf-8") + b"\x00")


def encode_osc_message(address: str, values: Iterable[float | int]) -> bytes:
    """Empaqueta un mensaje OSC 1.0 valido (solo floats/ints) sin dependencias externas."""
    vals = list(values)
    tags = "," + "".join("i" if isinstance(v, int) and not isinstance(v, bool) else "f" for v in vals)
    payload = bytearray()
    payload.extend(_osc_str(address))
    payload.extend(_osc_str(tags))
    for v in vals:
        if isinstance(v, int) and not isinstance(v, bool):
            payload.extend(struct.pack(">i", v))
        else:
            payload.extend(struct.pack(">f", float(v)))
    return bytes(payload)


def encode_osc_bundle(messages: list[bytes]) -> bytes:
    """Agrupa varios mensajes OSC en un #bundle para recepcion atomica en TouchDesigner."""
    buf = bytearray(b"#bundle\x00")
    buf.extend(struct.pack(">Q", 1))  # timetag = immediate
    for msg in messages:
        buf.extend(struct.pack(">i", len(msg)))
        buf.extend(msg)
    return bytes(buf)


class TDBridgeSettings(bpy.types.PropertyGroup):
    host: bpy.props.StringProperty(name="TD Host", default="127.0.0.1")
    port: bpy.props.IntProperty(name="UDP Port", default=9000, min=1024, max=65535)
    hz: bpy.props.IntProperty(name="Update Hz", default=30, min=5, max=120)
    target_object: bpy.props.PointerProperty(
        name="Extra Object",
        type=bpy.types.Object,
        description="Objeto opcional (ej. Light o Empty) para enviar sus coordenadas a POPs/Light COMP",
    )
    is_running: bpy.props.BoolProperty(name="Running", default=False)


_SOCKET: socket.socket | None = None


def _close_socket() -> None:
    global _SOCKET
    if _SOCKET is not None:
        try:
            _SOCKET.close()
        except OSError:
            pass
        _SOCKET = None


def _send_tick() -> float | None:
    scene = bpy.context.scene
    props: TDBridgeSettings | None = getattr(scene, "td_bridge", None)
    if props is None or not props.is_running:
        _close_socket()
        return None

    global _SOCKET
    if _SOCKET is None:
        _SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    msgs: list[bytes] = []
    cam = scene.camera
    if cam is not None:
        loc = cam.matrix_world.to_translation()
        # Conversion basica de ejes: Blender Z-up -> TouchDesigner Y-up (X, Z, -Y)
        rot = cam.matrix_world.to_euler("XYZ")
        focal = cam.data.lens if getattr(cam, "data", None) and hasattr(cam.data, "lens") else 50.0
        msgs.append(
            encode_osc_message(
                "/blender/cam",
                [
                    loc.x,
                    loc.z,
                    -loc.y,
                    math.degrees(rot.x) - 90.0,
                    math.degrees(rot.z),
                    math.degrees(rot.y),
                    float(focal),
                ],
            )
        )

    msgs.append(
        encode_osc_message(
            "/blender/timeline",
            [int(scene.frame_current), int(scene.frame_start), int(scene.frame_end), float(scene.render.fps)],
        )
    )

    if props.target_object is not None:
        obj = props.target_object
        oloc = obj.matrix_world.to_translation()
        orot = obj.matrix_world.to_euler("XYZ")
        msgs.append(
            encode_osc_message(
                f"/blender/obj/{obj.name}",
                [
                    oloc.x,
                    oloc.z,
                    -oloc.y,
                    math.degrees(orot.x),
                    math.degrees(orot.z),
                    math.degrees(orot.y),
                ],
            )
        )

    try:
        _SOCKET.sendto(encode_osc_bundle(msgs), (props.host, int(props.port)))
    except OSError as exc:
        print(f"[TD Bridge OSC] Error enviando UDP: {exc}")

    return 1.0 / max(1, int(props.hz))


class TDBRIDGE_OT_toggle(bpy.types.Operator):
    bl_idname = "td_bridge.toggle_osc"
    bl_label = "Toggle TouchDesigner OSC Sync"
    bl_description = "Inicia o detiene el envio de camara y frame hacia TouchDesigner"

    def execute(self, context: bpy.types.Context) -> set[str]:
        props = context.scene.td_bridge
        props.is_running = not props.is_running
        if props.is_running:
            if not bpy.app.timers.is_registered(_send_tick):
                bpy.app.timers.register(_send_tick, first_interval=0.05)
            self.report({"INFO"}, f"TD OSC Bridge activo -> {props.host}:{props.port}")
        else:
            if bpy.app.timers.is_registered(_send_tick):
                bpy.app.timers.unregister(_send_tick)
            _close_socket()
            self.report({"INFO"}, "TD OSC Bridge detenido")
        return {"FINISHED"}


class TDBRIDGE_PT_panel(bpy.types.Panel):
    bl_label = "TD Bridge (OSC)"
    bl_idname = "TDBRIDGE_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TD Bridge"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        props = context.scene.td_bridge

        col = layout.column(align=True)
        col.prop(props, "host")
        col.prop(props, "port")
        col.prop(props, "hz")
        col.separator()
        col.prop(props, "target_object")
        col.separator()

        label = "Stop OSC Sync" if props.is_running else "Start OSC Sync"
        icon = "PAUSE" if props.is_running else "PLAY"
        col.operator("td_bridge.toggle_osc", text=label, icon=icon)

        box = layout.box()
        box.label(text="Canales OSC en TouchDesigner:")
        box.label(text="/blender/cam (tx,ty,tz,rx,ry,rz,lens)")
        box.label(text="/blender/timeline (frame,start,end,fps)")


_CLASSES = (TDBridgeSettings, TDBRIDGE_OT_toggle, TDBRIDGE_PT_panel)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.td_bridge = bpy.props.PointerProperty(type=TDBridgeSettings)


def unregister() -> None:
    if bpy.app.timers.is_registered(_send_tick):
        bpy.app.timers.unregister(_send_tick)
    _close_socket()
    if hasattr(bpy.types.Scene, "td_bridge"):
        del bpy.types.Scene.td_bridge
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
