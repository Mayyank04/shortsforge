"""
Cinematic camera director for ShortForge AI Minecraft Studio.
Controls camera setups, focal lengths, look-at constraints, and keyframed camera movements.
"""
from __future__ import annotations

CAMERA_DIRECTOR_SCRIPT = """
def setup_cinematic_camera(cam_spec, target_pos=(0, 0, 1.2), total_frames=30):
    scene = bpy.context.scene
    
    # Target Empty for Look-At Constraint
    target = bpy.data.objects.new("CamTarget", None)
    scene.collection.objects.link(target)
    target.location = target_pos
    
    # Camera Data
    cam_data = bpy.data.cameras.new("CinematicCamera")
    shot_type = cam_spec.get('shot', 'medium_shot')
    
    # Focal lengths based on shot composition
    if shot_type in ['extreme_close_up', 'close_up']:
        cam_data.lens = 75.0
    elif shot_type in ['wide_shot', 'establishing_shot', 'low_angle']:
        cam_data.lens = 28.0
    else:
        cam_data.lens = 45.0
        
    cam_obj = bpy.data.objects.new("CinematicCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    # Track-To Constraint
    tt = cam_obj.constraints.new(type='TRACK_TO')
    tt.target = target
    tt.track_axis = 'TRACK_NEGATIVE_Z'
    tt.up_axis = 'UP_Y'
    
    dist = cam_spec.get('distance', 4.5)
    pitch_deg = cam_spec.get('pitch', 15.0)
    yaw_deg = cam_spec.get('yaw', 0.0)
    movement = cam_spec.get('movement', 'slow_dolly_in')
    
    # Calculate starting position relative to target
    pitch_rad = math.radians(pitch_deg)
    yaw_rad = math.radians(yaw_deg)
    
    x0 = target_pos[0] + dist * math.cos(pitch_rad) * math.sin(yaw_rad)
    y0 = target_pos[1] - dist * math.cos(pitch_rad) * math.cos(yaw_rad)
    z0 = target_pos[2] + dist * math.sin(pitch_rad)
    
    # Calculate ending position based on movement type
    if movement in ['dolly_in', 'slow_dolly_in']:
        end_dist = dist * 0.78
        x1 = target_pos[0] + end_dist * math.cos(pitch_rad) * math.sin(yaw_rad)
        y1 = target_pos[1] - end_dist * math.cos(pitch_rad) * math.cos(yaw_rad)
        z1 = target_pos[2] + end_dist * math.sin(pitch_rad)
    elif movement in ['dolly_out', 'slow_dolly_out']:
        end_dist = dist * 1.30
        x1 = target_pos[0] + end_dist * math.cos(pitch_rad) * math.sin(yaw_rad)
        y1 = target_pos[1] - end_dist * math.cos(pitch_rad) * math.cos(yaw_rad)
        z1 = target_pos[2] + end_dist * math.sin(pitch_rad)
    elif movement in ['orbit', 'pan_right']:
        yaw_end = yaw_rad + math.radians(18.0)
        x1 = target_pos[0] + dist * math.cos(pitch_rad) * math.sin(yaw_end)
        y1 = target_pos[1] - dist * math.cos(pitch_rad) * math.cos(yaw_end)
        z1 = z0
    elif movement in ['crane_down', 'crane']:
        x1, y1 = x0, y0
        z1 = max(target_pos[2] + 0.5, z0 - 1.8)
    elif movement in ['crane_up']:
        x1, y1 = x0, y0
        z1 = z0 + 1.8
    else:  # subtle cinematic drift
        x1 = x0 + 0.35
        y1 = y0 + 0.25
        z1 = z0 + 0.15
        
    # Animate Keyframes
    cam_obj.location = (x0, y0, z0)
    cam_obj.keyframe_insert(data_path="location", frame=1)
    
    cam_obj.location = (x1, y1, z1)
    cam_obj.keyframe_insert(data_path="location", frame=total_frames)
    
    return cam_obj
"""
