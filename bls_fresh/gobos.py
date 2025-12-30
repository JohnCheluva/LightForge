import bpy
import os
import bpy.utils.previews

# Global debug info
debug_msg = "Not initialized"

def get_addon_dir():
    """Get the addon directory"""
    return os.path.dirname(os.path.abspath(__file__))

def create_default_textures():
    """Create default textures if they don't exist"""
    addon_dir = get_addon_dir()
    textures_dir = os.path.join(addon_dir, "textures")
    gobos_dir = os.path.join(textures_dir, "gobos")
    icons_dir = os.path.join(textures_dir, "icons", "gobos")
    hdri_dir = os.path.join(textures_dir, "hdri")
    
    # Create directories
    os.makedirs(gobos_dir, exist_ok=True)
    os.makedirs(icons_dir, exist_ok=True)
    os.makedirs(hdri_dir, exist_ok=True)
    
    # Default gobo textures
    defaults = [
        ("softbox", (1.0, 1.0, 1.0, 1.0)),
        ("grid", (0.7, 0.7, 0.7, 1.0)),
        ("circle", (0.9, 0.8, 0.6, 1.0)),
        ("dots", (0.8, 0.9, 1.0, 1.0)),
        ("stripes", (1.0, 0.9, 0.8, 1.0)),
    ]
    
    for name, color in defaults:
        # Create a simple 128x128 image
        img = bpy.data.images.new(name, width=128, height=128)
        
        # Fill with pattern
        pixels = []
        for y in range(128):
            for x in range(128):
                if name == "softbox":
                    dx = (x - 64) / 64.0
                    dy = (y - 64) / 64.0
                    dist = (dx*dx + dy*dy) ** 0.5
                    intensity = max(0, 1 - dist)
                    px_color = (color[0] * intensity, color[1] * intensity, color[2] * intensity, 1.0)
                elif name == "grid":
                    if (x % 16 < 2) or (y % 16 < 2):
                        px_color = color
                    else:
                        px_color = (color[0]*0.3, color[1]*0.3, color[2]*0.3, 1.0)
                elif name == "circle":
                    dx = (x - 64) / 64.0
                    dy = (y - 64) / 64.0
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist < 0.4:
                        px_color = color
                    else:
                        px_color = (color[0]*0.4, color[1]*0.4, color[2]*0.4, 1.0)
                elif name == "dots":
                    if (x % 32 < 8) and (y % 32 < 8):
                        px_color = color
                    else:
                        px_color = (color[0]*0.5, color[1]*0.5, color[2]*0.5, 1.0)
                else:  # stripes
                    if (x // 16) % 2 == 0:
                        px_color = color
                    else:
                        px_color = (color[0]*0.6, color[1]*0.6, color[2]*0.6, 1.0)
                
                pixels.extend(px_color)
        
        img.pixels = pixels
        
        # Save PNG
        icon_path = os.path.join(icons_dir, f"{name}.png")
        tex_path = os.path.join(gobos_dir, f"{name}.png")
        
        img.filepath_raw = icon_path
        img.file_format = 'PNG'
        img.save()
        
        img.filepath_raw = tex_path
        img.save()
        
        bpy.data.images.remove(img)
    
    return len(defaults)

def load_gobo_icons(pcoll):
    """Load gobo icons into preview collection"""
    global debug_msg
    
    print("BLS: Loading gobo icons...")
    
    addon_dir = get_addon_dir()
    icons_dir = os.path.join(addon_dir, "textures", "icons", "gobos")
    
    # Create directories and default textures if needed
    if not os.path.exists(icons_dir):
        print("BLS: Creating default textures...")
        create_default_textures()
    
    # Clear existing previews
    pcoll.clear()
    
    items = []
    
    if os.path.exists(icons_dir):
        # Supported formats
        supported_ext = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tga')
        
        # Get all image files
        image_files = [f for f in os.listdir(icons_dir) 
                      if f.lower().endswith(supported_ext)]
        
        print(f"BLS: Found {len(image_files)} gobo icon files")
        
        for i, filename in enumerate(sorted(image_files)):
            name = os.path.splitext(filename)[0]
            filepath = os.path.join(icons_dir, filename)
            
            try:
                thumb = pcoll.load(name, filepath, 'IMAGE')
                items.append((name, name, filename, thumb.icon_id, i))
            except Exception as e:
                print(f"BLS: Failed to load '{filename}': {e}")
        
        debug_msg = f"Loaded {len(items)} gobo icons"
    else:
        debug_msg = "Gobo icons directory not found"
    
    # Store items
    pcoll.gobo_items = items if items else [("NONE", "No Textures", "Add textures", 0, 0)]
    
    print(f"BLS: {debug_msg}")
    return items

def load_hdri_icons(pcoll):
    """Load HDRI icons into preview collection"""
    print("BLS: Loading HDRI icons...")
    
    addon_dir = get_addon_dir()
    hdri_dir = os.path.join(addon_dir, "textures", "hdri")
    
    # Create directory if it doesn't exist
    os.makedirs(hdri_dir, exist_ok=True)
    
    # Clear existing previews
    pcoll.clear()
    
    items = []
    
    if os.path.exists(hdri_dir):
        # Supported HDRI formats
        supported_ext = ('.hdr', '.exr', '.jpg', '.jpeg', '.png', '.webp')
        
        # Get all HDRI files
        hdri_files = [f for f in os.listdir(hdri_dir) 
                     if f.lower().endswith(supported_ext)]
        
        print(f"BLS: Found {len(hdri_files)} HDRI files")
        
        for i, filename in enumerate(sorted(hdri_files)):
            name = os.path.splitext(filename)[0]
            filepath = os.path.join(hdri_dir, filename)
            
            try:
                thumb = pcoll.load(name, filepath, 'IMAGE')
                items.append((filename, name, filename, thumb.icon_id, i))
            except Exception as e:
                print(f"BLS: Failed to load HDRI '{filename}': {e}")
                # Try to load a placeholder if the HDRI itself fails
                try:
                    # Create a simple color preview
                    pcoll_key = f"hdri_{name}"
                    items.append((filename, name, filename, 'WORLD_DATA', i))
                except:
                    pass
    
    # Always add at least one item
    if not items:
        items.append(("NONE", "No HDRIs", "Add HDRIs to textures/hdri folder", 0, 0))
    
    # Store items
    pcoll.hdri_items = items
    
    print(f"BLS: Loaded {len(items)} HDRI previews")
    return items

def get_gobo_previews(self, context):
    """Callback for gobo previews"""
    from . import preview_collections
    
    if "main" in preview_collections:
        pcoll = preview_collections["main"]
        if hasattr(pcoll, 'gobo_items'):
            return pcoll.gobo_items
    
    return [("NONE", "Loading...", "Loading textures", 0, 0)]

def get_hdri_previews(self, context):
    """Callback for HDRI previews"""
    from . import preview_collections
    
    if "hdri" in preview_collections:
        pcoll = preview_collections["hdri"]
        if hasattr(pcoll, 'hdri_items'):
            return pcoll.hdri_items
    
    return [("NONE", "No HDRIs", "Add HDRIs to textures/hdri", 0, 0)]

def load_reflector_icons(pcoll):
    """Load reflector icons into preview collection"""
    print("BLS: Loading reflector icons...")
    
    addon_dir = get_addon_dir()
    icons_dir = os.path.join(addon_dir, "textures", "icons", "reflectors")
    
    # Create directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    # Clear existing previews
    pcoll.clear()
    
    items = []
    
    if os.path.exists(icons_dir):
        # Supported formats
        supported_ext = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tga')
        
        # Get all image files
        image_files = [f for f in os.listdir(icons_dir) 
                      if f.lower().endswith(supported_ext)]
        
        print(f"BLS: Found {len(image_files)} reflector icon files")
        
        for i, filename in enumerate(sorted(image_files)):
            name = os.path.splitext(filename)[0]
            filepath = os.path.join(icons_dir, filename)
            
            try:
                thumb = pcoll.load(name, filepath, 'IMAGE')
                items.append((name, name, filename, thumb.icon_id, i))
            except Exception as e:
                print(f"BLS: Failed to load reflector '{filename}': {e}")
    
    # Prioritize Silver
    silver_item = None
    for item in items:
        if item[0].upper() == 'SILVER':
            silver_item = item
            break
    
    
    # Default items if no icons found
    if not items:
        # Use standard Blender icons to represent materials
        items = [
            ("SILVER", "Silver", "Silver reflector", 'PLAY_REVERSE', 0),
            ("GOLD", "Gold", "Gold reflector", 'PLAY', 1),
            ("WHITE", "White", "White reflector", 'SHADING_BBOX', 2),
            ("BLACK", "Black", "Black flag", 'SHADING_BBOX', 3),
        ]
    
    # Store items
    pcoll.reflector_items = items
    
    print(f"BLS: Loaded {len(items)} reflector previews")
    return items

def get_reflector_previews(self, context):
    """Callback for reflector previews"""
    from . import preview_collections
    
    if "reflector" in preview_collections:
        pcoll = preview_collections["reflector"]
        if hasattr(pcoll, 'reflector_items'):
            return pcoll.reflector_items
    
    return [
        ("SILVER", "Silver", "Silver reflector", 'PLAY_REVERSE', 0),
        ("GOLD", "Gold", "Gold reflector", 'PLAY', 1),
        ("WHITE", "White", "White reflector", 'SHADING_BBOX', 2),
        ("BLACK", "Black", "Black flag", 'SHADING_BBOX', 3),
    ]

def update_gpu_device(self, context):
    """Auto-apply GPU settings when changed"""
    scene = context.scene
    scene.render.engine = 'CYCLES'
    
    # Access Cycles preferences
    cprefs = context.preferences.addons['cycles'].preferences
    
    if self.gpu_device == 'NONE':
        cprefs.compute_device_type = 'NONE'
        print("BLS: CPU rendering enabled")
        return
        
    # Set device type
    cprefs.compute_device_type = self.gpu_device # 'CUDA' or 'OPTIX'
    
    # Refresh devices
    cprefs.get_devices()
    
    # Enable all GPU devices
    for device in cprefs.devices:
        if device.type == self.gpu_device:
            device.use = True
        else:
            device.use = False
            
    # Configure Denoising
    if self.gpu_device == 'CUDA':
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        if hasattr(scene.cycles, "denoising_use_gpu"):
            scene.cycles.denoising_use_gpu = True
        print("BLS: GPU Ready: CUDA + OIDN")
        
    elif self.gpu_device == 'OPTIX':
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPTIX'
        print("BLS: GPU Ready: OptiX")
        
    scene.cycles.device = 'GPU'
    
    # Force redraw to show feedback if needed
    for area in context.screen.areas:
        area.tag_redraw()

# Operators
class BLS_OT_apply_gobo(bpy.types.Operator):
    bl_idname = "bls.apply_gobo"
    bl_label = "Apply Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        light = context.active_object
        if not light or light.type != 'LIGHT':
            self.report({'ERROR'}, "Please select a light object")
            return {'CANCELLED'}
        
        props = context.scene.bls_props
        texture_type = props.texture_type
        
        light.data.use_nodes = True
        nodes = light.data.node_tree.nodes
        links = light.data.node_tree.links
        nodes.clear()
        
        node_emission = nodes.new(type='ShaderNodeEmission')
        node_emission.location = (0, 0)
        node_output = nodes.new(type='ShaderNodeOutputLight')
        node_output.location = (200, 0)
        links.new(node_emission.outputs['Emission'], node_output.inputs['Surface'])
        
        if texture_type == 'IMAGE':
            self.setup_image_texture(nodes, links, node_emission, props.active_gobo_texture)
        elif texture_type == 'PROCEDURAL':
            if props.procedural_type == 'GRADIENT':
                self.setup_gradient_texture(nodes, links, node_emission)
            elif props.procedural_type == 'NOISE':
                self.setup_noise_texture(nodes, links, node_emission)
        
        # Apply Camera Visibility
        light.visible_camera = props.gobo_camera_visible
        
        return {'FINISHED'}

    def setup_image_texture(self, nodes, links, node_emission, texture_name):
        if texture_name == "NONE":
            return
        
        addon_dir = get_addon_dir()
        tex_dir = os.path.join(addon_dir, "textures", "gobos")
        
        # Find texture file
        filepath = None
        for ext in ['.png', '.jpg', '.jpeg', '.webp', '.exr']:
            test_path = os.path.join(tex_dir, f"{texture_name}{ext}")
            if os.path.exists(test_path):
                filepath = test_path
                break
        
        if not filepath:
            self.report({'WARNING'}, f"Texture '{texture_name}' not found")
            return
        
        try:
            img = bpy.data.images.load(filepath, check_existing=True)
            
            node_tex = nodes.new(type='ShaderNodeTexImage')
            node_tex.image = img
            node_tex.location = (-300, 0)
            
            node_mapping = nodes.new(type='ShaderNodeMapping')
            node_mapping.location = (-500, 0)
            node_mapping.inputs['Scale'].default_value = (1, 1, 1)
            
            node_coord = nodes.new(type='ShaderNodeTexCoord')
            node_coord.location = (-700, 0)
            
            links.new(node_coord.outputs['UV'], node_mapping.inputs['Vector'])
            links.new(node_mapping.outputs['Vector'], node_tex.inputs['Vector'])
            links.new(node_tex.outputs['Color'], node_emission.inputs['Color'])
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load texture: {e}")

    def setup_gradient_texture(self, nodes, links, node_emission):
        node_ramp = nodes.new(type='ShaderNodeValToRGB')
        node_ramp.location = (-300, 0)
        
        # Set B-Spline interpolation
        node_ramp.color_ramp.interpolation = 'B_SPLINE'
        
        # Clear existing elements and add 3 positions
        ramp = node_ramp.color_ramp
        # Set first element position
        ramp.elements[0].position = 0.3
        ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        # Set second element position
        ramp.elements[1].position = 0.7
        ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        # Add middle element
        middle = ramp.elements.new(0.5)
        middle.color = (0.5, 0.5, 0.5, 1.0)
        
        node_grad = nodes.new(type='ShaderNodeTexGradient')
        node_grad.location = (-500, 0)
        node_grad.gradient_type = 'LINEAR'
        
        node_mapping = nodes.new(type='ShaderNodeMapping')
        node_mapping.location = (-700, 0)
        node_mapping.inputs['Scale'].default_value = (2, 2, 2)
        
        node_coord = nodes.new(type='ShaderNodeTexCoord')
        node_coord.location = (-900, 0)
        
        links.new(node_coord.outputs['UV'], node_mapping.inputs['Vector'])
        links.new(node_mapping.outputs['Vector'], node_grad.inputs['Vector'])
        links.new(node_grad.outputs['Color'], node_ramp.inputs['Fac'])
        links.new(node_ramp.outputs['Color'], node_emission.inputs['Color'])

    def setup_noise_texture(self, nodes, links, node_emission):
        node_ramp = nodes.new(type='ShaderNodeValToRGB')
        node_ramp.location = (-300, 0)
        
        # Set B-Spline interpolation for smooth noise
        node_ramp.color_ramp.interpolation = 'B_SPLINE'
        
        node_noise = nodes.new(type='ShaderNodeTexNoise')
        node_noise.location = (-500, 0)
        node_noise.inputs['Scale'].default_value = 10.0
        node_noise.inputs['Detail'].default_value = 5.0
        
        node_mapping = nodes.new(type='ShaderNodeMapping')
        node_mapping.location = (-700, 0)
        node_mapping.inputs['Scale'].default_value = (5, 5, 5)
        
        node_coord = nodes.new(type='ShaderNodeTexCoord')
        node_coord.location = (-900, 0)
        
        links.new(node_coord.outputs['UV'], node_mapping.inputs['Vector'])
        links.new(node_mapping.outputs['Vector'], node_noise.inputs['Vector'])
        links.new(node_noise.outputs['Fac'], node_ramp.inputs['Fac'])
        links.new(node_ramp.outputs['Color'], node_emission.inputs['Color'])


class BLS_OT_reload_icons(bpy.types.Operator):
    bl_idname = "bls.reload_icons"
    bl_label = "Reload All Icons"
    
    def execute(self, context):
        from . import preview_collections
        
        if "main" in preview_collections:
            load_gobo_icons(preview_collections["main"])
        
        if "hdri" in preview_collections:
            load_hdri_icons(preview_collections["hdri"])
        
        # Force UI redraw
        for area in context.screen.areas:
            area.tag_redraw()
        
        self.report({'INFO'}, "All icons reloaded")
        return {'FINISHED'}

class BLS_OT_generate_defaults(bpy.types.Operator):
    bl_idname = "bls.generate_defaults"
    bl_label = "Generate Default Textures"
    
    def execute(self, context):
        num_created = create_default_textures()
        
        # Reload icons
        from . import preview_collections
        if "main" in preview_collections:
            load_gobo_icons(preview_collections["main"])
        
        self.report({'INFO'}, f"Created {num_created} default textures")
        return {'FINISHED'}

class BLS_OT_debug_info(bpy.types.Operator):
    bl_idname = "bls.debug_info"
    bl_label = "Debug Info"
    
    def execute(self, context):
        addon_dir = get_addon_dir()
        icons_dir = os.path.join(addon_dir, "textures", "icons", "gobos")
        hdri_dir = os.path.join(addon_dir, "textures", "hdri")
        
        info = f"Addon: {addon_dir}\n"
        info += f"Icons: {icons_dir} ({'Exists' if os.path.exists(icons_dir) else 'Missing'})\n"
        info += f"HDRI: {hdri_dir} ({'Exists' if os.path.exists(hdri_dir) else 'Missing'})\n"
        
        if os.path.exists(icons_dir):
            files = os.listdir(icons_dir)
            info += f"Icon files: {len(files)}\n"
            for f in files[:5]:
                info += f"  {f}\n"
        
        if os.path.exists(hdri_dir):
            files = os.listdir(hdri_dir)
            info += f"HDRI files: {len(files)}\n"
            for f in files[:5]:
                info += f"  {f}\n"
        
        self.report({'INFO'}, info)
        print(f"BLS DEBUG:\n{info}")
        return {'FINISHED'}

class BLS_OT_apply_hdri_from_lib(bpy.types.Operator):
    bl_idname = "bls.apply_hdri_from_lib"
    bl_label = "Apply HDRI"
    
    def execute(self, context):
        props = context.scene.bls_props
        filename = props.active_hdri_texture
        
        if filename == "NONE":
            self.report({'ERROR'}, "No HDRI selected")
            return {'CANCELLED'}
        
        addon_dir = get_addon_dir()
        hdri_dir = os.path.join(addon_dir, "textures", "hdri")
        filepath = os.path.join(hdri_dir, filename)
        
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"HDRI not found: {filename}")
            return {'CANCELLED'}
        
        # Setup world
        world = context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            context.scene.world = world
        
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        
        node_output = nodes.new('ShaderNodeOutputWorld')
        node_bg = nodes.new('ShaderNodeBackground')
        node_env = nodes.new('ShaderNodeTexEnvironment')
        node_mapping = nodes.new('ShaderNodeMapping')
        node_coord = nodes.new('ShaderNodeTexCoord')
        
        try:
            img = bpy.data.images.load(filepath)
            node_env.image = img
        except:
            self.report({'ERROR'}, "Failed to load HDRI")
            return {'CANCELLED'}
        
        links.new(node_coord.outputs['Generated'], node_mapping.inputs['Vector'])
        links.new(node_mapping.outputs['Vector'], node_env.inputs['Vector'])
        links.new(node_env.outputs['Color'], node_bg.inputs['Color'])
        links.new(node_bg.outputs['Background'], node_output.inputs['Surface'])
        
        # Name nodes for real-time update callbacks
        node_bg.name = "BLS_Background"
        node_mapping.name = "BLS_Mapping"
        
        # Set values from props
        props = context.scene.bls_props
        node_bg.inputs['Strength'].default_value = props.hdri_intensity
        node_mapping.inputs['Rotation'].default_value[2] = props.hdri_rotation * (3.14159 / 180.0)
        
        # Arrange nodes
        node_output.location = (400, 0)
        node_bg.location = (200, 0)
        node_env.location = (0, 0)
        node_mapping.location = (-200, 0)
        node_coord.location = (-400, 0)
        
        self.report({'INFO'}, f"Applied HDRI: {filename}")
        return {'FINISHED'}

# Property Group
def update_hdri_env(self, context):
    world = context.scene.world
    if not world or not world.use_nodes:
        return
    
    nodes = world.node_tree.nodes
    
    # Update Intensity (Background node)
    node_bg = nodes.get("BLS_Background")
    if node_bg:
        node_bg.inputs['Strength'].default_value = context.scene.bls_props.hdri_intensity
        
    # Update Rotation (Mapping node)
    node_mapping = nodes.get("BLS_Mapping")
    if node_mapping:
        # Index 2 is Z rotation
        node_mapping.inputs['Rotation'].default_value[2] = context.scene.bls_props.hdri_rotation * (3.14159 / 180.0)

def update_camera_visibility(self, context):
    """Live update for camera visibility"""
    # Try to find the active light
    light_obj = context.active_object
    if light_obj and light_obj.type == 'LIGHT':
        # Correctly access Object-level property
        light_obj.visible_camera = self.gobo_camera_visible
    else:
        # Fallback: try to find selected light if active is not light
        for obj in context.selected_objects:
            if obj.type == 'LIGHT':
                obj.visible_camera = self.gobo_camera_visible
                break

class BLS_Properties(bpy.types.PropertyGroup):
    # HDRI Properties
    hdri_intensity: bpy.props.FloatProperty(
        name="Intensity",
        description="Brightness of the HDRI",
        default=1.0,
        min=0.0,
        max=10.0,
        update=update_hdri_env
    )
    
    hdri_rotation: bpy.props.FloatProperty(
        name="Rotation",
        description="Rotation of the HDRI environment (Z-axis)",
        default=0.0,
        min=0.0,
        max=360.0,
        update=update_hdri_env
    )
    
    # Active selected categories
    texture_type: bpy.props.EnumProperty(
        name="Texture Type",
        items=[
            ('IMAGE', "Image", "Image texture from library"),
            ('PROCEDURAL', "Procedural", "Procedural textures"),
        ],
        default='IMAGE'
    )
    
    procedural_type: bpy.props.EnumProperty(
        name="Procedural Type",
        items=[
            ('GRADIENT', "Gradient", "Gradient light texture"),
            ('NOISE', "Noise", "Noise-based light texture"),
        ],
        default='GRADIENT'
    )
    
    active_gobo_texture: bpy.props.EnumProperty(
        name="Gobo Texture",
        description="Select a gobo texture",
        items=get_gobo_previews
    )

    gobo_camera_visible: bpy.props.BoolProperty(
        name="Camera Visibility",
        description="Make the light texture visible to camera (Primary Visibility)",
        default=False,
        update=update_camera_visibility
    )
    
    active_hdri_texture: bpy.props.EnumProperty(
        name="HDRI",
        description="Select an HDRI",
        items=get_hdri_previews
    )
    
    active_reflector: bpy.props.EnumProperty(
        name="Reflector",
        description="Select a reflector type",
        items=get_reflector_previews
    )

    gpu_device: bpy.props.EnumProperty(
        name="GPU Device",
        items=[
            ('NONE', "CPU / None", "Use CPU for rendering"),
            ('CUDA', "CUDA (GPU)", "Use CUDA and OpenImageDenoise"),
            ('OPTIX', "OptiX (GPU)", "Use OptiX and OptiX Denoiser"),
        ],
        default='NONE',
        update=update_gpu_device
    )

    use_motion_blur: bpy.props.BoolProperty(
        name="Motion Blur",
        description="Enable motion blur in render",
        default=False
    )

    dof_active: bpy.props.BoolProperty(
        name="Depth of Field",
        description="Enable Depth of Field for active camera",
        default=False
    )

    dof_target: bpy.props.PointerProperty(
        name="Focus Object",
        type=bpy.types.Object,
        description="Object to focus on"
    )

# Classes
classes = (
    BLS_Properties,
    BLS_OT_apply_gobo,
    BLS_OT_reload_icons,
    BLS_OT_generate_defaults,
    BLS_OT_debug_info,
    BLS_OT_apply_hdri_from_lib,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            pass
    
    # Register property group
    if not hasattr(bpy.types.Scene, 'bls_props'):
        bpy.types.Scene.bls_props = bpy.props.PointerProperty(type=BLS_Properties)

def unregister():
    if hasattr(bpy.types.Scene, 'bls_props'):
        del bpy.types.Scene.bls_props
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass