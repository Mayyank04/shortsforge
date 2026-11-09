"""
Animation director and articulated character rig builder for ShortForge AI Minecraft Studio.
Builds canonical articulated characters (Head, Torso, Left/Right Arms, Left/Right Legs)
and keyframes 16 cinematic animation actions.
"""
from __future__ import annotations

ANIMATION_DIRECTOR_SCRIPT = """
def create_articulated_character(char_spec, base_pos=(0, 0, 0), facing_deg=0.0):
    char_id = char_spec['id']
    root = bpy.data.objects.new(f"{char_id}_root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = base_pos
    root.rotation_euler = (0, 0, math.radians(facing_deg))
    
    scale = char_spec.get('proportions', {}).get('height', 1.8) / 1.8
    skin_rgba = hex_to_rgba(char_spec.get('skin_tone', '#d49b6a'))
    cloth1_rgba = hex_to_rgba(char_spec.get('clothing_primary', '#2563eb'))
    cloth2_rgba = hex_to_rgba(char_spec.get('clothing_secondary', '#1e293b'))
    hair_rgba = hex_to_rgba(char_spec.get('hair_color', '#451a03'))
    
    skin_mat = create_voxel_material(f"{char_id}_skin", skin_rgba, roughness=0.85)
    cloth1_mat = create_voxel_material(f"{char_id}_cloth1", cloth1_rgba, roughness=0.8)
    cloth2_mat = create_voxel_material(f"{char_id}_cloth2", cloth2_rgba, roughness=0.8)
    hair_mat = create_voxel_material(f"{char_id}_hair", hair_rgba, roughness=0.9)
    
    # 1. Torso
    torso_h = 0.65 * scale
    torso_w = 0.46 * scale
    torso_d = 0.24 * scale
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.70 * scale + torso_h / 2))
    torso = bpy.context.active_object
    torso.name = f"{char_id}_torso"
    torso.scale = (torso_w, torso_d, torso_h)
    torso.data.materials.append(cloth1_mat)
    torso.parent = root
    
    # 2. Head
    head_size = 0.48 * scale
    head_z = 0.70 * scale + torso_h + head_size / 2
    bpy.ops.mesh.primitive_cube_add(size=head_size, location=(0, 0, head_z))
    head = bpy.context.active_object
    head.name = f"{char_id}_head"
    head.data.materials.append(skin_mat)
    head.parent = torso
    
    # Hair cap
    if char_spec.get('hair_style') != 'none':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, head_z + head_size * 0.25))
        hair = bpy.context.active_object
        hair.name = f"{char_id}_hair"
        hair.scale = (head_size * 1.05, head_size * 1.05, head_size * 0.55)
        hair.data.materials.append(hair_mat)
        hair.parent = head

    # Eyes
    eye_col = (0.2, 0.5, 0.9, 1.0) if char_id in ['mini', 'steve'] else ((0.8, 0.2, 0.9, 1.0) if char_id == 'shadow' else (0.8, 0.1, 0.1, 1.0))
    eye_mat = create_voxel_material(f"{char_id}_eye", eye_col, emission_color=eye_col if char_id in ['shadow', 'iron_golem'] else None, emission_strength=4.0 if char_id in ['shadow', 'iron_golem'] else 0.0)
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side * 0.12 * scale, -head_size * 0.52, head_z))
        eye = bpy.context.active_object
        eye.scale = (0.08 * scale, 0.02 * scale, 0.08 * scale)
        eye.data.materials.append(eye_mat)
        eye.parent = head
        
    # 3. Arms
    arm_w, arm_d, arm_h = 0.18 * scale, 0.18 * scale, 0.62 * scale
    shoulder_z = 0.70 * scale + torso_h - arm_w / 2
    
    # Left Arm
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-torso_w / 2 - arm_w / 2, 0, shoulder_z - arm_h / 2))
    l_arm = bpy.context.active_object
    l_arm.name = f"{char_id}_arm_l"
    l_arm.scale = (arm_w, arm_d, arm_h)
    l_arm.data.materials.append(cloth1_mat)
    l_arm.parent = torso
    
    # Right Arm
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(torso_w / 2 + arm_w / 2, 0, shoulder_z - arm_h / 2))
    r_arm = bpy.context.active_object
    r_arm.name = f"{char_id}_arm_r"
    r_arm.scale = (arm_w, arm_d, arm_h)
    r_arm.data.materials.append(cloth1_mat)
    r_arm.parent = torso
    
    # 4. Legs
    leg_w, leg_d, leg_h = 0.18 * scale, 0.18 * scale, 0.68 * scale
    leg_z = leg_h / 2
    
    # Left Leg
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.11 * scale, 0, leg_z))
    l_leg = bpy.context.active_object
    l_leg.name = f"{char_id}_leg_l"
    l_leg.scale = (leg_w, leg_d, leg_h)
    l_leg.data.materials.append(cloth2_mat)
    l_leg.parent = root
    
    # Right Leg
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.11 * scale, 0, leg_z))
    r_leg = bpy.context.active_object
    r_leg.name = f"{char_id}_leg_r"
    r_leg.scale = (leg_w, leg_d, leg_h)
    r_leg.data.materials.append(cloth2_mat)
    r_leg.parent = root
    
    return {
        "root": root, "torso": torso, "head": head,
        "arm_l": l_arm, "arm_r": r_arm, "leg_l": l_leg, "leg_r": r_leg
    }

def animate_character_action(parts, action_name='walking', total_frames=30):
    root = parts['root']
    arm_l = parts['arm_l']
    arm_r = parts['arm_r']
    leg_l = parts['leg_l']
    leg_r = parts['leg_r']
    torso = parts['torso']
    head = parts['head']
    
    if action_name in ['walking', 'running']:
        amp = 45.0 if action_name == 'running' else 28.0
        cycles = 3.0 if action_name == 'running' else 2.0
        for f in range(1, total_frames + 1):
            phase = (f / total_frames) * math.pi * 2.0 * cycles
            # Sinusoidal arm and leg swing
            arm_l.rotation_euler = (math.sin(phase) * math.radians(amp), 0, 0)
            arm_r.rotation_euler = (-math.sin(phase) * math.radians(amp), 0, 0)
            leg_l.rotation_euler = (-math.sin(phase) * math.radians(amp), 0, 0)
            leg_r.rotation_euler = (math.sin(phase) * math.radians(amp), 0, 0)
            
            arm_l.keyframe_insert(data_path="rotation_euler", frame=f)
            arm_r.keyframe_insert(data_path="rotation_euler", frame=f)
            leg_l.keyframe_insert(data_path="rotation_euler", frame=f)
            leg_r.keyframe_insert(data_path="rotation_euler", frame=f)
            
        if action_name == 'running':
            torso.rotation_euler = (math.radians(14.0), 0, 0)
            torso.keyframe_insert(data_path="rotation_euler", frame=1)
            
    elif action_name == 'waving':
        # Right arm raised and waving
        for f in range(1, total_frames + 1):
            wave_x = math.sin((f / total_frames) * math.pi * 6.0) * math.radians(18.0)
            arm_r.rotation_euler = (math.radians(-140.0), wave_x, 0)
            arm_r.keyframe_insert(data_path="rotation_euler", frame=f)
            
    elif action_name == 'celebrating':
        # Both arms raised in victory
        for f in range(1, total_frames + 1):
            jump_z = math.sin((f / total_frames) * math.pi * 4.0) * 0.15
            arm_l.rotation_euler = (math.radians(-135.0), math.radians(-20.0), 0)
            arm_r.rotation_euler = (math.radians(-135.0), math.radians(20.0), 0)
            arm_l.keyframe_insert(data_path="rotation_euler", frame=f)
            arm_r.keyframe_insert(data_path="rotation_euler", frame=f)
            
    elif action_name in ['looking_scared', 'falling']:
        # Recoil back
        torso.rotation_euler = (math.radians(-18.0), 0, 0)
        torso.keyframe_insert(data_path="rotation_euler", frame=1)
        head.rotation_euler = (math.radians(25.0), 0, 0)
        head.keyframe_insert(data_path="rotation_euler", frame=1)
        arm_l.rotation_euler = (math.radians(-65.0), math.radians(-30.0), 0)
        arm_r.rotation_euler = (math.radians(-65.0), math.radians(30.0), 0)
        arm_l.keyframe_insert(data_path="rotation_euler", frame=1)
        arm_r.keyframe_insert(data_path="rotation_euler", frame=1)
        
    elif action_name in ['reaching', 'carrying']:
        # Arms forward
        arm_l.rotation_euler = (math.radians(-85.0), 0, 0)
        arm_r.rotation_euler = (math.radians(-85.0), 0, 0)
        arm_l.keyframe_insert(data_path="rotation_euler", frame=1)
        arm_r.keyframe_insert(data_path="rotation_euler", frame=1)
        
    elif action_name == 'pointing':
        # Right arm extended forward
        arm_r.rotation_euler = (math.radians(-90.0), 0, 0)
        arm_r.keyframe_insert(data_path="rotation_euler", frame=1)
        
    elif action_name == 'fighting':
        # Combat swing
        for f in range(1, total_frames + 1):
            swing = math.sin((f / total_frames) * math.pi * 4.0) * math.radians(65.0)
            arm_r.rotation_euler = (math.radians(-40.0) + swing, 0, 0)
            arm_r.keyframe_insert(data_path="rotation_euler", frame=f)
"""
