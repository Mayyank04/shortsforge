"""
Blender 3D geographical scene renderer for GeoGlobeTales-style videos.
Constructs 3D Earth globe, shaders, 3D pins, 3D flags, terrain bumps, and renders frames.
"""
from __future__ import annotations
import os
import sys
import json
import math
import shutil
import glob
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from .geo.geo_resolver import GeoContext, LandmarkPin, TradeRoute, CountryHighlight
from .geo.data_manager import BASE_DIR, GEO_DIR, TEXTURES_DIR, ensure_geo_assets

class BlenderRenderError(RuntimeError):
    """Raised when Blender rendering fails or exits with a non-zero status."""
    def __init__(self, message: str, returncode: int | None = None, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def find_blender_binary() -> Path:
    """
    Finds the Blender executable across macOS, Linux (Kaggle/cloud), and Windows.
    Resolution order:
    1. BLENDER_BIN environment variable
    2. shutil.which("blender")
    3. Platform-specific known paths:
       - macOS:
         /Applications/Blender.app/Contents/MacOS/Blender
         /opt/homebrew/bin/blender
         /usr/local/bin/blender
         ~/Applications/Blender.app/Contents/MacOS/Blender
       - Linux:
         /usr/bin/blender
         /usr/local/bin/blender
         /snap/bin/blender
         /kaggle/working/blender/blender
         /opt/blender/blender
       - Windows:
         %PROGRAMFILES%\\Blender Foundation\\Blender *\\blender.exe
         %LOCALAPPDATA%\\Programs\\Blender Foundation\\Blender *\\blender.exe
    Raises FileNotFoundError if Blender executable cannot be found.
    """
    # 1. Environment variable override
    env_bin = os.getenv("BLENDER_BIN")
    if env_bin:
        p = Path(env_bin).expanduser().resolve()
        if p.is_file() and (os.name == "nt" or os.access(p, os.X_OK)):
            return p
        raise FileNotFoundError(
            f"BLENDER_BIN environment variable is set to '{env_bin}', but the file does not exist or is not executable."
        )

    # 2. PATH lookup
    which_bin = shutil.which("blender")
    if which_bin:
        p = Path(which_bin).resolve()
        if p.is_file():
            return p

    # 3. Platform candidate search
    candidates: list[Path] = []
    if sys.platform == "darwin":
        candidates.extend([
            Path("/Applications/Blender.app/Contents/MacOS/Blender"),
            Path("/opt/homebrew/bin/blender"),
            Path("/usr/local/bin/blender"),
            Path.home() / "Applications/Blender.app/Contents/MacOS/Blender",
        ])
    elif sys.platform.startswith("linux"):
        candidates.extend([
            Path("/usr/bin/blender"),
            Path("/usr/local/bin/blender"),
            Path("/snap/bin/blender"),
            Path("/kaggle/working/blender/blender"),
            Path("/opt/blender/blender"),
        ])
    elif sys.platform == "win32":
        for pf_var in ["PROGRAMFILES", "PROGRAMFILES(X86)"]:
            pf = os.getenv(pf_var)
            if pf:
                candidates.extend(Path(pf).glob("Blender Foundation/Blender */blender.exe"))
        local_app = os.getenv("LOCALAPPDATA")
        if local_app:
            candidates.extend(Path(local_app).glob("Programs/Blender Foundation/Blender */blender.exe"))

    for c in candidates:
        if c.is_file() and (sys.platform == "win32" or os.access(c, os.X_OK)):
            return c if sys.platform == "win32" else c.resolve()

    raise FileNotFoundError(
        "Blender executable not found. Please install Blender or set the BLENDER_BIN environment variable."
    )

def get_blender_version(blender_path: Path | str | None = None) -> str:
    """Executes blender --version and returns the first line (e.g. 'Blender 5.2.3 LTS')."""
    bin_path = Path(blender_path) if blender_path else find_blender_binary()
    try:
        res = subprocess.run(
            [str(bin_path), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=True
        )
        lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
        return lines[0] if lines else "Unknown Blender Version"
    except Exception as exc:
        raise BlenderRenderError(f"Failed to query Blender version from {bin_path}: {exc}") from exc

def verify_blender_available() -> tuple[Path, str]:
    """Verifies that Blender is installed, executable, and can report its version."""
    bin_path = find_blender_binary()
    version = get_blender_version(bin_path)
    return bin_path, version

def _resolve_default_blender_bin() -> str:
    try:
        return str(find_blender_binary())
    except FileNotFoundError:
        return "blender"

BLENDER_BIN = _resolve_default_blender_bin()

def geo_to_pixel(lon: float, lat: float, width: int = 4096, height: int = 2048) -> tuple[int, int]:
    """Converts (lon, lat) to equirectangular pixel coordinates."""
    x = int((lon + 180.0) / 360.0 * width)
    y = int((90.0 - lat) / 180.0 * height)
    return (max(0, min(x, width - 1)), max(0, min(y, height - 1)))

def generate_scene_texture(
    geo_context: GeoContext,
    highlighted_country_names: list[str],
    include_trade_routes: bool = False,
    output_path: Path | None = None
) -> Path:
    """
    Creates a customized 4K equirectangular texture map with glowing country borders,
    semi-transparent country fills, and trade routes.
    """
    ensure_geo_assets()
    base_tex_path = TEXTURES_DIR / "earth_color_4k.jpg"
    base_img = Image.open(base_tex_path).convert("RGBA")
    W, H = base_img.size

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Filter highlights to active countries in this scene
    active_highlights = [
        h for h in geo_context.highlights
        if not highlighted_country_names or h.name in highlighted_country_names
    ]

    for h in active_highlights:
        fill_col = h.fill_rgba
        outline_col = h.outline_rgba

        for poly in h.polygons:
            for ring in poly:
                pts = [geo_to_pixel(pt[0], pt[1], W, H) for pt in ring]
                if len(pts) >= 3:
                    # Draw glowing border outer halo
                    draw.polygon(pts, fill=fill_col, outline=outline_col, width=6)

    # Draw trade routes if requested
    if include_trade_routes and geo_context.trade_routes:
        for route in geo_context.trade_routes:
            pts = [geo_to_pixel(pt[1], pt[0], W, H) for pt in route.points]
            if len(pts) >= 2:
                # Outer cyan glow
                draw.line(pts, fill=(0, 240, 255, 120), width=16)
                # Inner bright line
                draw.line(pts, fill=(255, 255, 255, 240), width=6)
                # Route node points
                for p in pts:
                    draw.ellipse((p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8), fill=(255, 255, 255, 255), outline=(0, 220, 255, 255), width=3)

    combined = Image.alpha_composite(base_img, overlay).convert("RGB")
    dest = output_path or (GEO_DIR / "temp_scene_tex.jpg")
    dest.parent.mkdir(parents=True, exist_ok=True)
    combined.save(dest, quality=92)
    return dest

def render_blender_scene(
    scene_spec_dict: dict,
    geo_context_dict: dict,
    texture_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
    preview: bool = False,
    blender_bin: str | Path | None = None
) -> Path:
    """
    Invokes Blender headlessly via a Python sub-script to render the 3D scene.
    Supports macOS, Linux (Kaggle), and Windows.
    """
    bin_to_use = Path(blender_bin) if blender_bin else find_blender_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bump_path = TEXTURES_DIR / "earth_bump_4k.jpg"
    water_path = TEXTURES_DIR / "earth_water_4k.png"

    # Resolve flag path if applicable
    flag_path = None
    if scene_spec_dict.get("asset_type") == "flag_banner" or "Gibraltar" in scene_spec_dict.get("highlight_countries", []):
        for h in geo_context_dict.get("highlights", []):
            if h.get("name") == "United Kingdom" and h.get("flag_path"):
                flag_path = h.get("flag_path")
                break

    blender_payload = {
        "width": width // 2 if preview else width,
        "height": height // 2 if preview else height,
        "texture_path": Path(texture_path).resolve().as_posix(),
        "bump_path": Path(bump_path).resolve().as_posix() if bump_path.exists() else None,
        "water_path": Path(water_path).resolve().as_posix() if water_path.exists() else None,
        "flag_path": Path(flag_path).resolve().as_posix() if flag_path and Path(flag_path).exists() else None,
        "output_path": Path(output_path).resolve().as_posix(),
        "lat": scene_spec_dict.get("lat", 36.14),
        "lon": scene_spec_dict.get("lon", -5.35),
        "camera_distance": scene_spec_dict.get("camera_distance", 2.4),
        "camera_pitch": scene_spec_dict.get("camera_pitch", 45.0),
        "camera_yaw": scene_spec_dict.get("camera_yaw", 0.0),
        "asset_type": scene_spec_dict.get("asset_type", "globe_satellite"),
        "animation_type": scene_spec_dict.get("animation_type", "earth_rotation")
    }

    # Generate isolated Blender python script
    blender_script = f"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix

params = json.loads('''{json.dumps(blender_payload)}''')

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = params['width']
scene.render.resolution_y = params['height']

R = 2.0

def geo_to_3d(lat, lon, r=R):
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    x = r * math.cos(lat_r) * math.cos(lon_r)
    y = r * math.cos(lat_r) * math.sin(lon_r)
    z = r * math.sin(lat_r)
    return Vector((x, y, z))

# Earth Sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=64, ring_count=64, location=(0,0,0))
earth = bpy.context.active_object
bpy.ops.object.shade_smooth()

# Material
mat = bpy.data.materials.new('EarthMat')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
bsdf = nodes.get('Principled BSDF')

# Base Color
color_img = bpy.data.images.load(params['texture_path'])
tex_node = nodes.new('ShaderNodeTexImage')
tex_node.image = color_img
links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

# Bump Normal
if params.get('bump_path'):
    bump_img = bpy.data.images.load(params['bump_path'])
    bump_tex = nodes.new('ShaderNodeTexImage')
    bump_tex.image = bump_img
    bump_node = nodes.new('ShaderNodeBump')
    bump_node.inputs['Distance'].default_value = 0.045
    links.new(bump_tex.outputs['Color'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])

# Specular Roughness
if params.get('water_path'):
    water_img = bpy.data.images.load(params['water_path'])
    water_tex = nodes.new('ShaderNodeTexImage')
    water_tex.image = water_img
    # Oceans have low roughness (shiny), land has high roughness
    links.new(water_tex.outputs['Color'], bsdf.inputs['Roughness'])

earth.data.materials.append(mat)

# 3D Pin Marker
target_pos = geo_to_3d(params['lat'], params['lon'], r=R)
normal = target_pos.normalized()

if params['asset_type'] in ['pin_marker', 'flag_banner', 'isthmus_border']:
    # Glowing pin sphere
    pin_pos = geo_to_3d(params['lat'], params['lon'], r=R + 0.075)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.038, segments=32, ring_count=32, location=pin_pos)
    pin_head = bpy.context.active_object
    pin_mat = bpy.data.materials.new('PinMat')
    pin_mat.use_nodes = True
    p_bsdf = pin_mat.node_tree.nodes.get('Principled BSDF')
    p_bsdf.inputs['Base Color'].default_value = (1.0, 0.15, 0.25, 1.0)
    p_bsdf.inputs['Emission Color'].default_value = (1.0, 0.2, 0.3, 1.0)
    p_bsdf.inputs['Emission Strength'].default_value = 4.0
    pin_head.data.materials.append(pin_mat)

    # Pin stem
    stem_mid = geo_to_3d(params['lat'], params['lon'], r=R + 0.038)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.075, location=stem_mid)
    stem = bpy.context.active_object
    stem.rotation_mode = 'QUATERNION'
    stem.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(normal)
    stem_mat = bpy.data.materials.new('StemMat')
    stem_mat.use_nodes = True
    s_bsdf = stem_mat.node_tree.nodes.get('Principled BSDF')
    s_bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 1.0, 1.0)
    stem.data.materials.append(stem_mat)

# 3D Floating Flag
if params['asset_type'] == 'flag_banner' and params.get('flag_path'):
    flag_pos = geo_to_3d(params['lat'], params['lon'], r=R + 0.16)
    bpy.ops.mesh.primitive_plane_add(size=0.10, location=flag_pos)
    flag_obj = bpy.context.active_object
    flag_obj.scale = (1.5, 1.0, 1.0)
    flag_obj.rotation_mode = 'QUATERNION'
    flag_obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(normal)

    flag_mat = bpy.data.materials.new('FlagMat')
    flag_mat.use_nodes = True
    f_nodes = flag_mat.node_tree.nodes
    f_links = flag_mat.node_tree.links
    f_bsdf = f_nodes.get('Principled BSDF')
    flag_img = bpy.data.images.load(params['flag_path'])
    f_tex = f_nodes.new('ShaderNodeTexImage')
    f_tex.image = flag_img
    f_links.new(f_tex.outputs['Color'], f_bsdf.inputs['Base Color'])
    f_bsdf.inputs['Emission Color'].default_value = (1, 1, 1, 1)
    f_links.new(f_tex.outputs['Color'], f_bsdf.inputs['Emission Color'])
    f_bsdf.inputs['Emission Strength'].default_value = 0.8
    flag_obj.data.materials.append(flag_mat)

# Camera System
cam_dist = params['camera_distance']
pitch_rad = math.radians(params['camera_pitch'])
yaw_rad = math.radians(params['camera_yaw'])

# Camera positioned in spherical coordinates relative to target
# Shift camera along surface normal by pitch and yaw
lat_offset = params['lat'] - (params['camera_pitch'] * 0.28)
lon_offset = params['lon'] + (params['camera_yaw'] * 0.25)
cam_pos = geo_to_3d(lat_offset, lon_offset, r=R * cam_dist)

cam_data = bpy.data.cameras.new('Camera')
cam_data.lens = 45.0  # Cinematic focal length
cam_obj = bpy.data.objects.new('Camera', cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = cam_pos

# Track to Target
track = cam_obj.constraints.new(type='TRACK_TO')
target_empty = bpy.data.objects.new('Target', None)
scene.collection.objects.link(target_empty)
target_empty.location = target_pos
track.target = target_empty
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# Sunlight
light_data = bpy.data.lights.new('Sun', type='SUN')
light_data.energy = 4.2
light_obj = bpy.data.objects.new('Sun', light_data)
scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (math.radians(35), math.radians(25), math.radians(45))

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
            err_tail = "\\n".join(proc.stderr.strip().splitlines()[-25:])
            out_tail = "\\n".join(proc.stdout.strip().splitlines()[-25:])
            raise BlenderRenderError(
                f"Blender failed with exit code {proc.returncode}.\\n"
                f"Stderr tail:\\n{err_tail}\\n"
                f"Stdout tail:\\n{out_tail}",
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise BlenderRenderError(
                f"Blender completed with exit code 0 but target file was not created: {output_path}",
                returncode=0,
                stdout=proc.stdout,
                stderr=proc.stderr
            )
    finally:
        try:
            os.remove(script_file)
        except OSError:
            pass

    return output_path

