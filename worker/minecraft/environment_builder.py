"""
Procedural voxel environment generator for ShortForge AI Minecraft Studio.
Builds 11 biomes and structures in Blender Python using block primitives and procedural materials.
"""
from __future__ import annotations

ENV_BUILDER_SCRIPT = """
def create_voxel_material(name, color_rgba, roughness=0.8, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color_rgba
    bsdf.inputs['Roughness'].default_value = roughness
    if emission_color and emission_strength > 0:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission_color
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat

def build_environment(env_type='Village', time_of_day='day'):
    # Base ground plane (30x30 block grid)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.5))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.scale = (32.0, 32.0, 1.0)
    
    if env_type in ['Village', 'Farm', 'Forest']:
        ground_mat = create_voxel_material('GrassMat', (0.22, 0.58, 0.18, 1.0), roughness=0.9)
    elif env_type == 'Snow':
        ground_mat = create_voxel_material('SnowMat', (0.92, 0.95, 0.98, 1.0), roughness=0.7)
    elif env_type == 'Desert':
        ground_mat = create_voxel_material('SandMat', (0.86, 0.78, 0.48, 1.0), roughness=0.95)
    elif env_type == 'Nether':
        ground_mat = create_voxel_material('NetherrackMat', (0.45, 0.12, 0.14, 1.0), roughness=0.85)
    else:
        ground_mat = create_voxel_material('StoneMat', (0.42, 0.42, 0.45, 1.0), roughness=0.8)
    ground.data.materials.append(ground_mat)

    # Cobblestone pathway for Village
    if env_type in ['Village', 'Castle']:
        path_mat = create_voxel_material('CobbleMat', (0.35, 0.35, 0.38, 1.0), roughness=0.85)
        for y_step in range(-12, 13, 2):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, y_step, 0.05))
            path_tile = bpy.context.active_object
            path_tile.scale = (2.2, 1.8, 0.1)
            path_tile.data.materials.append(path_mat)

    # Village Houses & Structures
    if env_type == 'Village':
        wood_mat = create_voxel_material('OakWoodMat', (0.42, 0.28, 0.16, 1.0), roughness=0.75)
        plank_mat = create_voxel_material('OakPlankMat', (0.65, 0.50, 0.30, 1.0), roughness=0.8)
        roof_mat = create_voxel_material('CobbleRoofMat', (0.28, 0.28, 0.30, 1.0), roughness=0.85)
        glass_mat = create_voxel_material('GlassMat', (0.75, 0.88, 0.95, 0.6), roughness=0.1)

        # House 1 (Left background)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5.5, 4.0, 1.75))
        h1 = bpy.context.active_object
        h1.scale = (4.0, 5.0, 3.5)
        h1.data.materials.append(plank_mat)

        # Roof
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5.5, 4.0, 3.8))
        r1 = bpy.context.active_object
        r1.scale = (4.6, 5.6, 0.8)
        r1.data.materials.append(roof_mat)

        # House 2 (Right background)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.5, 3.0, 1.75))
        h2 = bpy.context.active_object
        h2.scale = (4.0, 4.5, 3.5)
        h2.data.materials.append(wood_mat)

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.5, 3.0, 3.8))
        r2 = bpy.context.active_object
        r2.scale = (4.6, 5.1, 0.8)
        r2.data.materials.append(roof_mat)

        # Central Monument / Beacon Pedestal
        pedestal_mat = create_voxel_material('ObsidianMat', (0.12, 0.08, 0.18, 1.0), roughness=0.4)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 2.5, 0.6))
        ped = bpy.context.active_object
        ped.scale = (2.0, 2.0, 1.2)
        ped.data.materials.append(pedestal_mat)

        # Beacon Crystal Core
        crystal_mat = create_voxel_material(
            'CrystalMat', (0.2, 0.85, 0.95, 1.0),
            roughness=0.1,
            emission_color=(0.2, 0.9, 1.0, 1.0),
            emission_strength=4.5
        )
        bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 2.5, 1.5))
        core = bpy.context.active_object
        core.data.materials.append(crystal_mat)

        # Street Lanterns
        lamp_mat = create_voxel_material('LampPostMat', (0.2, 0.2, 0.2, 1.0))
        glow_mat = create_voxel_material('LanternGlow', (1.0, 0.85, 0.4, 1.0), emission_color=(1.0, 0.8, 0.3, 1.0), emission_strength=5.0)
        for lx in [-2.5, 2.5]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=2.4, location=(lx, -1.0, 1.2))
            post = bpy.context.active_object
            post.data.materials.append(lamp_mat)
            bpy.ops.mesh.primitive_cube_add(size=0.35, location=(lx, -1.0, 2.5))
            lantern = bpy.context.active_object
            lantern.data.materials.append(glow_mat)

    # Trees for Forest and Village border
    if env_type in ['Village', 'Forest', 'Mountain']:
        trunk_mat = create_voxel_material('TrunkMat', (0.35, 0.22, 0.12, 1.0))
        leaves_mat = create_voxel_material('LeavesMat', (0.15, 0.48, 0.15, 1.0))
        tree_locs = [(-7.0, -4.0), (7.5, -3.5), (-6.5, 9.0), (6.0, 9.5)]
        for tx, ty in tree_locs:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=4.0, location=(tx, ty, 2.0))
            trunk = bpy.context.active_object
            trunk.data.materials.append(trunk_mat)
            # Foliage box
            bpy.ops.mesh.primitive_cube_add(size=2.8, location=(tx, ty, 4.2))
            foliage = bpy.context.active_object
            foliage.data.materials.append(leaves_mat)

    # Nether specifics
    if env_type == 'Nether':
        lava_mat = create_voxel_material('LavaMat', (0.95, 0.35, 0.05, 1.0), emission_color=(1.0, 0.3, 0.0, 1.0), emission_strength=8.0)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 6.0, 0.1))
        lava = bpy.context.active_object
        lava.scale = (16.0, 6.0, 0.2)
        lava.data.materials.append(lava_mat)

    # Lighting based on time_of_day
    setup_environment_lighting(time_of_day)

def setup_environment_lighting(time_of_day='day'):
    scene = bpy.context.scene
    
    # Sun light
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    sun_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    scene.collection.objects.link(sun_obj)
    
    if time_of_day == 'day':
        light_data.energy = 4.2
        light_data.color = (1.0, 0.98, 0.92)
        sun_obj.rotation_euler = (math.radians(45), math.radians(25), math.radians(35))
    elif time_of_day == 'dusk':
        light_data.energy = 2.8
        light_data.color = (1.0, 0.55, 0.30)
        sun_obj.rotation_euler = (math.radians(15), math.radians(65), math.radians(20))
    elif time_of_day == 'dawn':
        light_data.energy = 3.5
        light_data.color = (1.0, 0.85, 0.65)
        sun_obj.rotation_euler = (math.radians(20), math.radians(35), math.radians(70))
    elif time_of_day == 'storm':
        light_data.energy = 1.0
        light_data.color = (0.25, 0.35, 0.60)
        sun_obj.rotation_euler = (math.radians(60), math.radians(10), math.radians(45))
        # Add lightning flash fill light
        flash_data = bpy.data.lights.new(name="LightningFlash", type='POINT')
        flash_data.energy = 350.0
        flash_data.color = (0.7, 0.85, 1.0)
        flash_obj = bpy.data.objects.new(name="LightningFlash", object_data=flash_data)
        scene.collection.objects.link(flash_obj)
        flash_obj.location = (2.0, 3.0, 8.0)
    else:  # night
        light_data.energy = 0.8
        light_data.color = (0.20, 0.28, 0.55)
        sun_obj.rotation_euler = (math.radians(50), math.radians(10), math.radians(40))
"""
