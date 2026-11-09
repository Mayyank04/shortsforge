"""
Headless Blender renderer for ShortForge AI Minecraft Story Studio.
Executes procedural voxel environments, articulated characters, cinematic cameras,
and keyframe animations to render production frames.
"""
from __future__ import annotations
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

from worker.blender_render import find_blender_binary, BlenderRenderError
from .environment_builder import ENV_BUILDER_SCRIPT
from .camera_director import CAMERA_DIRECTOR_SCRIPT
from .animation_director import ANIMATION_DIRECTOR_SCRIPT
from .metadata import SceneSpec, CanonicalCharacter

def render_minecraft_scene(
    scene_spec: SceneSpec,
    characters: list[CanonicalCharacter],
    output_frame_path: Path,
    width: int = 1080,
    height: int = 1920,
    preview: bool = False,
    blender_bin: Path | str | None = None
) -> Path:
    """
    Renders a single 3D scene frame using headless Blender.
    """
    bin_to_use = Path(blender_bin) if blender_bin else find_blender_binary()
    output_frame_path.parent.mkdir(parents=True, exist_ok=True)

    char_dict = {c.id: c.model_dump() for c in characters}
    actions_dict = [a.model_dump() for a in scene_spec.character_actions]
    cam_dict = scene_spec.camera.model_dump()

    payload = {
        "width": width // 2 if preview else width,
        "height": height // 2 if preview else height,
        "environment": scene_spec.environment,
        "time_of_day": scene_spec.time_of_day,
        "characters": char_dict,
        "active_character_ids": scene_spec.characters,
        "actions": actions_dict,
        "camera": cam_dict,
        "output_path": output_frame_path.resolve().as_posix(),
        "total_frames": 30,
        "render_frame": 15
    }

    blender_script = f"""
import bpy, math, json
from mathutils import Vector, Matrix

params = json.loads('''{json.dumps(payload)}''')

def hex_to_rgba(hex_str):
    c = hex_str.lstrip('#')
    if len(c) == 3:
        c = ''.join([x*2 for x in c])
    try:
        r = int(c[0:2], 16) / 255.0
        g = int(c[2:4], 16) / 255.0
        b = int(c[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    except:
        return (0.5, 0.5, 0.5, 1.0)

# Reset factory scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = params['width']
scene.render.resolution_y = params['height']
scene.frame_start = 1
scene.frame_end = params['total_frames']
scene.frame_current = params['render_frame']

{ENV_BUILDER_SCRIPT}
{CAMERA_DIRECTOR_SCRIPT}
{ANIMATION_DIRECTOR_SCRIPT}

# 1. Build Environment
build_environment(env_type=params['environment'], time_of_day=params['time_of_day'])

# 2. Build Characters
char_parts_map = {{}}
char_positions = {{}}

active_ids = params['active_character_ids']
all_chars = params['characters']

# Default spacing along X axis if multiple characters present
num_chars = len(active_ids)
start_x = -((num_chars - 1) * 1.5) / 2.0

for i, cid in enumerate(active_ids):
    if cid in all_chars:
        cspec = all_chars[cid]
        # Check if custom action position is specified
        pos = (start_x + i * 1.5, 0.0, 0.0)
        facing = 0.0
        action_name = 'walking'
        
        for act in params['actions']:
            if act['character_id'] == cid:
                if act.get('position'):
                    pos = tuple(act['position'])
                facing = act.get('facing_angle', 0.0)
                action_name = act.get('action', 'walking')
                break
                
        parts = create_articulated_character(cspec, base_pos=pos, facing_deg=facing)
        char_parts_map[cid] = parts
        char_positions[cid] = pos
        animate_character_action(parts, action_name=action_name, total_frames=params['total_frames'])

# 3. Setup Cinematic Camera
target_focal_pos = (0.0, 0.0, 1.2)
focus_id = params['camera'].get('focus', '')
if focus_id in char_positions:
    target_focal_pos = (char_positions[focus_id][0], char_positions[focus_id][1], 1.2)

setup_cinematic_camera(params['camera'], target_pos=target_focal_pos, total_frames=params['total_frames'])

# Render Still Frame
scene.render.filepath = params['output_path']
bpy.ops.render.render(write_still=True)
"""

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(blender_script)
        script_file = tf.name

    try:
        proc = subprocess.run(
            [str(bin_to_use), "-b", "--python", script_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180
        )
        if proc.returncode != 0:
            err_tail = "\n".join(proc.stderr.strip().splitlines()[-20:])
            out_tail = "\n".join(proc.stdout.strip().splitlines()[-20:])
            raise BlenderRenderError(
                f"Minecraft Blender scene failed with exit code {proc.returncode}.\n"
                f"Stderr:\n{err_tail}\n"
                f"Stdout:\n{out_tail}",
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr
            )
        if not output_frame_path.exists() or output_frame_path.stat().st_size == 0:
            raise BlenderRenderError(
                f"Blender finished with exit code 0 but frame was not saved: {output_frame_path}",
                returncode=0,
                stdout=proc.stdout,
                stderr=proc.stderr
            )
    finally:
        try:
            os.remove(script_file)
        except OSError:
            pass

    return output_frame_path
