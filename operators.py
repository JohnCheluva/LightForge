import bpy
import os

def ensure_collection_linked(context, obj, collection_name):
    """Ensure object is linked to a specific collection, unlinking from others if needed"""
    # Create or get collection
    if collection_name in bpy.data.collections:
        col = bpy.data.collections[collection_name]
    else:
        col = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(col)
        
    # Link object if not already linked
    if obj.name not in col.objects:
        col.objects.link(obj)
        
    # Unlink from other collections (optional, keeps hierarchy clean)
    for other_col in obj.users_collection:
        if other_col != col:
            other_col.objects.unlink(obj)
class BLS_OT_setup_product_lighting(bpy.types.Operator):
    bl_idname = "bls.setup_product_lighting"
    bl_label = "3 Point Lighting"
    bl_options = {'REGISTER', 'UNDO'}

    def ensure_collection(self, context, collection_name):
        return ensure_collection_linked(context, collection_name)

    def execute(self, context):
        context.scene.render.engine = 'CYCLES'
        
        # Validation: Must select an object
        selected = context.selected_objects
        if not selected:
            self.report({'ERROR'}, "Please select an object to target")
            return {'CANCELLED'}
        
        target = selected[0]
        target_loc = target.location
        
        # Create lights relative to target location
        # Pos: (X, Y, Z) - Y+ is Back, Y- is Front
        lights_data = [
            ("Key_Light", (0 + target_loc.x, -3 + target_loc.y, 1 + target_loc.z), 75, 3),   # Front
            ("Fill_Light", (2 + target_loc.x, -1 + target_loc.y, 2 + target_loc.z), 150, 3),  # Left/Right
            ("Rim_Light", (0 + target_loc.x, 3 + target_loc.y, 1 + target_loc.z), 300, 3),   # Back
        ]
        
        for name, loc, energy, size in lights_data:
            bpy.ops.object.light_add(type='AREA', location=loc)
            light = context.active_object
            light.name = name
            light.data.energy = energy
            light.data.size = size
            
            # Ensure proper collection
            ensure_collection_linked(context, light, "Lights")
            
            # Add track-to constraint
            constraint = light.constraints.new(type='TRACK_TO')
            constraint.target = target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
        
        return {'FINISHED'}

class BLS_OT_setup_hdri(bpy.types.Operator):
    bl_idname = "bls.setup_hdri"
    bl_label = "Setup HDRI"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
            
        world = context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            context.scene.world = world
        
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        
        node_output = nodes.new(type='ShaderNodeOutputWorld')
        node_bg = nodes.new(type='ShaderNodeBackground')
        node_env = nodes.new(type='ShaderNodeTexEnvironment')
        node_mapping = nodes.new(type='ShaderNodeMapping')
        node_coord = nodes.new(type='ShaderNodeTexCoord')
        
        try:
            img = bpy.data.images.load(self.filepath)
            node_env.image = img
        except:
            self.report({'ERROR'}, "Could not load image")
            return {'CANCELLED'}
            
        links.new(node_coord.outputs['Generated'], node_mapping.inputs['Vector'])
        links.new(node_mapping.outputs['Vector'], node_env.inputs['Vector'])
        links.new(node_env.outputs['Color'], node_bg.inputs['Color'])
        links.new(node_bg.outputs['Background'], node_output.inputs['Surface'])
        
        # Name nodes for real-time update callbacks
        node_bg.name = "BLS_Background"
        node_mapping.name = "BLS_Mapping"
        
        # Set default values from props
        props = context.scene.bls_props
        node_bg.inputs['Strength'].default_value = props.hdri_intensity
        node_mapping.inputs['Rotation'].default_value[2] = props.hdri_rotation * (3.14159 / 180.0)
        
        # Arrange nodes
        node_output.location = (400, 0)
        node_bg.location = (200, 0)
        node_env.location = (0, 0)
        node_mapping.location = (-200, 0)
        node_coord.location = (-400, 0)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class BLS_OT_add_reflector(bpy.types.Operator):
    bl_idname = "bls.add_reflector"
    bl_label = "Add Reflector"
    bl_options = {'REGISTER', 'UNDO'}
    
    material_type: bpy.props.EnumProperty(
        items=[
            ('SILVER', "Silver", ""),
            ('GOLD', "Gold", ""),
            ('WHITE', "White", ""),
            ('BLACK', "Black Flag", ""),
        ],
        default='WHITE'
    )

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        reflector = context.active_object
        reflector.name = f"Reflector_{self.material_type}"
        
        # Ensure proper collection
        ensure_collection_linked(context, reflector, "Reflectors")
        
        # Ensure proper collection
        ensure_collection_linked(context, reflector, "Reflectors")
        
        mat_name = f"Reflector_{self.material_type}"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()
            
            node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            node_output = nodes.new(type='ShaderNodeOutputMaterial')
            mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
            
            if self.material_type == 'SILVER':
                node_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
                node_bsdf.inputs['Metallic'].default_value = 1.0
                node_bsdf.inputs['Roughness'].default_value = 0.1
            elif self.material_type == 'GOLD':
                node_bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.336, 1)
                node_bsdf.inputs['Metallic'].default_value = 1.0
                node_bsdf.inputs['Roughness'].default_value = 0.1
            elif self.material_type == 'WHITE':
                node_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
                node_bsdf.inputs['Metallic'].default_value = 0.0
                node_bsdf.inputs['Roughness'].default_value = 0.5
            elif self.material_type == 'BLACK':
                node_bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
                node_bsdf.inputs['Metallic'].default_value = 0.0
                node_bsdf.inputs['Roughness'].default_value = 1.0
        
        if reflector.data.materials:
            reflector.data.materials[0] = mat
        else:
            reflector.data.materials.append(mat)
            
        return {'FINISHED'}

class BLS_OT_set_gpu_render(bpy.types.Operator):
    bl_idname = "bls.set_gpu_render"
    bl_label = "Set GPU Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.bls_props
        scene = context.scene
        scene.render.engine = 'CYCLES'
        
        # Access Cycles preferences
        cprefs = context.preferences.addons['cycles'].preferences
        
        if props.gpu_device == 'NONE':
            cprefs.compute_device_type = 'NONE'
            self.report({'INFO'}, "CPU rendering enabled")
            return {'FINISHED'}
            
        # Set device type
        cprefs.compute_device_type = props.gpu_device # 'CUDA' or 'OPTIX'
        
        # Refresh devices
        cprefs.get_devices()
        
        # Enable all GPU devices
        for device in cprefs.devices:
            if device.type == props.gpu_device:
                device.use = True
            else:
                device.use = False
                
        # Configure Denoising
        if props.gpu_device == 'CUDA':
            scene.cycles.use_denoising = True
            scene.cycles.denoiser = 'OPENIMAGEDENOISE'
            # Enable GPU acceleration for OIDN if available (Blender 4.1+)
            if hasattr(scene.cycles, "denoising_use_gpu"):
                scene.cycles.denoising_use_gpu = True
            self.report({'INFO'}, "GPU Ready: CUDA + OIDN (GPU Enabled)")
            
        elif props.gpu_device == 'OPTIX':
            scene.cycles.use_denoising = True
            scene.cycles.denoiser = 'OPTIX'
            self.report({'INFO'}, "GPU Ready: OptiX + OptiX Denoiser")
            
        scene.cycles.device = 'GPU'
        return {'FINISHED'}



class BLS_OT_sync_camera_settings(bpy.types.Operator):
    bl_idname = "bls.sync_camera_settings"
    bl_label = "Sync Camera Settings"
    
    def execute(self, context):
        props = context.scene.bls_props
        cam = context.scene.camera
        if not cam or cam.type != 'CAMERA':
            return {'CANCELLED'}
            
        # Update Motion Blur
        context.scene.render.use_motion_blur = props.use_motion_blur
        
        # Update DOF
        cam.data.dof.use_dof = props.dof_active
        if props.dof_target:
            cam.data.dof.focus_object = props.dof_target
            
        return {'FINISHED'}

class BLS_OT_select_light(bpy.types.Operator):
    bl_idname = "bls.select_light"
    bl_label = "Select Light"
    bl_options = {'REGISTER', 'UNDO'}
    
    light_name: bpy.props.StringProperty()

    def execute(self, context):
        if self.light_name in bpy.data.objects:
            bpy.ops.object.select_all(action='DESELECT')
            obj = bpy.data.objects[self.light_name]
            obj.select_set(True)
            context.view_layer.objects.active = obj
        return {'FINISHED'}

class BLS_OT_auto_group_lights(bpy.types.Operator):
    bl_idname = "bls.auto_group_lights"
    bl_label = "Auto Group Lights"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        view_layer = context.view_layer
        
        if not hasattr(view_layer, "lightgroups"):
            self.report({'WARNING'}, "Light Groups not supported")
            return {'CANCELLED'}
            
        for obj in context.scene.objects:
            if obj.type == 'LIGHT':
                group_name = obj.name
                lg = view_layer.lightgroups.get(group_name)
                if not lg:
                    lg = view_layer.lightgroups.new(name=group_name)
                obj.lightgroup = group_name
                
        self.report({'INFO'}, "Lights grouped")
        return {'FINISHED'}

class BLS_OT_add_camera(bpy.types.Operator):
    bl_idname = "bls.add_camera"
    bl_label = "Add Camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    focal_length: bpy.props.FloatProperty(default=50.0)

    def execute(self, context):
        bpy.ops.object.camera_add(location=(0, -5, 1))
        cam = context.active_object
        cam.data.lens = self.focal_length
        cam.name = f"Camera_{int(self.focal_length)}mm"
        cam.data.passepartout_alpha = 1.0 # Set black borders
        context.scene.camera = cam
        return {'FINISHED'}

class BLS_OT_set_render_quality(bpy.types.Operator):
    bl_idname = "bls.set_render_quality"
    bl_label = "Set Quality"
    bl_options = {'REGISTER', 'UNDO'}
    
    quality: bpy.props.EnumProperty(
        items=[
            ('DRAFT', "Draft", ""),
            ('MEDIUM', "Medium", ""),
            ('HIGH', "High", ""),
            ('ULTRA', "Ultra", ""),
        ],
        default='DRAFT'
    )

    def execute(self, context):
        scene = context.scene
        scene.render.engine = 'CYCLES'
        
        if self.quality == 'DRAFT':
            scene.cycles.samples = 32
            scene.cycles.use_denoising = True
            scene.cycles.max_bounces = 4
            scene.cycles.diffuse_bounces = 4
            scene.cycles.glossy_bounces = 4
            scene.cycles.transmission_bounces = 4
            scene.cycles.volume_bounces = 0
            scene.render.resolution_percentage = 50
            # Fast GI Approximation bounce counts (user controls on/off)
            if hasattr(scene.cycles, 'ao_bounces'):
                scene.cycles.ao_bounces = 1
                scene.cycles.ao_bounces_render = 1
        elif self.quality == 'MEDIUM':
            scene.cycles.samples = 500
            scene.cycles.use_denoising = True
            scene.cycles.max_bounces = 8
            scene.cycles.diffuse_bounces = 8
            scene.cycles.glossy_bounces = 8
            scene.cycles.transmission_bounces = 8
            scene.cycles.volume_bounces = 2
            scene.render.resolution_percentage = 100
            # Fast GI Approximation bounce counts (user controls on/off)
            if hasattr(scene.cycles, 'ao_bounces'):
                scene.cycles.ao_bounces = 2
                scene.cycles.ao_bounces_render = 2
        elif self.quality == 'HIGH':
            scene.cycles.samples = 600
            scene.cycles.use_denoising = True
            scene.cycles.max_bounces = 12
            scene.cycles.diffuse_bounces = 12
            scene.cycles.glossy_bounces = 12
            scene.cycles.transmission_bounces = 12
            scene.cycles.volume_bounces = 4
            scene.render.resolution_percentage = 100
            # Fast GI Approximation bounce counts (user controls on/off)
            if hasattr(scene.cycles, 'ao_bounces'):
                scene.cycles.ao_bounces = 3
                scene.cycles.ao_bounces_render = 3
        elif self.quality == 'ULTRA':
            scene.cycles.samples = 1024
            scene.cycles.use_denoising = True
            scene.cycles.max_bounces = 32
            scene.cycles.diffuse_bounces = 32
            scene.cycles.glossy_bounces = 32
            scene.cycles.transmission_bounces = 32
            scene.cycles.volume_bounces = 12
            scene.render.resolution_percentage = 100
            # Fast GI Approximation bounce counts (user controls on/off)
            if hasattr(scene.cycles, 'ao_bounces'):
                scene.cycles.ao_bounces = 4
                scene.cycles.ao_bounces_render = 4
            
        self.report({'INFO'}, f"Quality: {self.quality}")
        return {'FINISHED'}

class BLS_OT_set_resolution(bpy.types.Operator):
    bl_idname = "bls.set_resolution"
    bl_label = "Set Resolution"
    bl_options = {'REGISTER', 'UNDO'}
    
    res_x: bpy.props.IntProperty()
    res_y: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.render.resolution_x = self.res_x
        context.scene.render.resolution_y = self.res_y
        context.scene.render.resolution_percentage = 100
        return {'FINISHED'}

class BLS_OT_create_tracked_light(bpy.types.Operator):
    bl_idname = "bls.create_tracked_light"
    bl_label = "Create Light"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'ERROR'}, "Please select an object to track")
            return {'CANCELLED'}
        
        target = selected[0]
        
        # Create light at Z=1 above the target
        light_loc = (target.location.x, target.location.y, target.location.z + 1)
        bpy.ops.object.light_add(type='AREA', location=light_loc)
        light = context.active_object
        light.name = f"Tracked_Light_{target.name}"
        light.data.energy = 500
        light.data.size = 1
        
        # Ensure proper collection
        ensure_collection_linked(context, light, "Lights")
        
        # Ensure proper collection
        ensure_collection_linked(context, light, "Lights")
        
        # Add track-to constraint
        constraint = light.constraints.new(type='TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
        self.report({'INFO'}, f"Created light tracking {target.name}")
        return {'FINISHED'}

class BLS_OT_create_camera_from_view(bpy.types.Operator):
    bl_idname = "bls.create_camera_from_view"
    bl_label = "Create Camera from View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the 3D viewport
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        # Get the view matrix
                        rv3d = area.spaces.active.region_3d
                        view_matrix = rv3d.view_matrix.inverted()
                        
                        # Create camera
                        bpy.ops.object.camera_add()
                        cam = context.active_object
                        cam.name = "Camera_FromView"
                        cam.matrix_world = view_matrix
                        cam.data.lens = 50
                        cam.data.passepartout_alpha = 1.0 # Set black borders
                        
                        # Set as active camera
                        context.scene.camera = cam
                        
                        self.report({'INFO'}, "Created camera from viewport")
                        return {'FINISHED'}
        
        self.report({'ERROR'}, "No 3D viewport found")
        return {'CANCELLED'}

class BLS_OT_add_reflector_from_selection(bpy.types.Operator):
    bl_idname = "bls.add_reflector_from_selection"
    bl_label = "Add Reflector"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.bls_props
        material_type = props.active_reflector.upper()
        
        # Default to SILVER if no valid selection
        if material_type not in ['SILVER', 'GOLD', 'WHITE', 'BLACK']:
            material_type = 'SILVER'
        
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        reflector = context.active_object
        reflector.name = f"Reflector_{material_type}"
        
        # Ensure proper collection
        ensure_collection_linked(context, reflector, "Reflectors")
        
        mat_name = f"Reflector_{material_type}"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()
            
            node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            node_output = nodes.new(type='ShaderNodeOutputMaterial')
            mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
            
            if material_type == 'SILVER':
                node_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
                node_bsdf.inputs['Metallic'].default_value = 1.0
                node_bsdf.inputs['Roughness'].default_value = 0.1
            elif material_type == 'GOLD':
                node_bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.336, 1)
                node_bsdf.inputs['Metallic'].default_value = 1.0
                node_bsdf.inputs['Roughness'].default_value = 0.1
            elif material_type == 'WHITE':
                node_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
                node_bsdf.inputs['Metallic'].default_value = 0.0
                node_bsdf.inputs['Roughness'].default_value = 0.5
            elif material_type == 'BLACK':
                node_bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
                node_bsdf.inputs['Metallic'].default_value = 0.0
                node_bsdf.inputs['Roughness'].default_value = 1.0
        
        if reflector.data.materials:
            reflector.data.materials[0] = mat
        else:
            reflector.data.materials.append(mat)
        
        self.report({'INFO'}, f"Added {material_type} reflector")
        return {'FINISHED'}

class BLS_OT_create_cyclorama(bpy.types.Operator):
    bl_idname = "bls.create_cyclorama"
    bl_label = "Create Cyclorama"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        target_size = 5.0
        target_loc = (0, 0, 0)
        
        if selected:
            target = selected[0]
            target_loc = target.location
            target_size = max(target.dimensions) * 4
            
        # Create base plane
        bpy.ops.mesh.primitive_plane_add(size=target_size, location=target_loc)
        cyc = context.active_object
        cyc.name = "Studio_Cyclorama"
        
        # Enter edit mode to extrude back edges
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Select back edge (aligned with Y+)
        bpy.ops.object.mode_set(mode='OBJECT')
        for edge in cyc.data.edges:
            v1 = cyc.data.vertices[edge.vertices[0]].co
            v2 = cyc.data.vertices[edge.vertices[1]].co
            if v1.y > 0 and v2.y > 0:
                edge.select = True
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, target_size/2)})
        
        # Smooth with bevel
        bpy.ops.object.mode_set(mode='OBJECT')
        bev = cyc.modifiers.new(name="CycBevel", type='BEVEL')
        bev.width = target_size / 4
        bev.segments = 10
        bev.limit_method = 'ANGLE'
        
        # Assign Studio Material
        mat_name = "Studio_Backdrop_Mat"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()
            
            node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            node_output = nodes.new(type='ShaderNodeOutputMaterial')
            mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
            
            # Mid Gray Color, 0.5 Metallic, 0.5 Roughness
            node_bsdf.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 0.5
            node_bsdf.inputs['Roughness'].default_value = 0.5
        
        if cyc.data.materials:
            cyc.data.materials[0] = mat
        else:
            cyc.data.materials.append(mat)
        
        bpy.ops.object.shade_smooth()
        self.report({'INFO'}, "Created Studio Backdrop with Material")
        return {'FINISHED'}

class BLS_OT_create_shadow_catcher(bpy.types.Operator):
    bl_idname = "bls.create_shadow_catcher"
    bl_label = "Create Shadow Catcher"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        target_loc = (0, 0, 0)
        target_size = 10.0
        
        if selected:
            target = selected[0]
            target_loc = target.location
            target_size = max(target.dimensions) * 6
            
        # Create plane below object
        bpy.ops.mesh.primitive_plane_add(size=target_size, location=(target_loc[0], target_loc[1], target_loc[2] - 0.001))
        ground = context.active_object
        ground.name = "Shadow_Catcher"
        
        # Set as shadow catcher
        ground.is_shadow_catcher = True
        
        # Enable transparency
        context.scene.render.film_transparent = True
        
        self.report({'INFO'}, "Shadow Catcher Enabled")
        return {'FINISHED'}

class BLS_OT_apply_reflector_material(bpy.types.Operator):
    bl_idname = "bls.apply_reflector_material"
    bl_label = "Apply Material to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.bls_props
        material_type = props.active_reflector.upper()
        
        # Default to SILVER if no valid selection
        if material_type not in ['SILVER', 'GOLD', 'WHITE', 'BLACK']:
            material_type = 'SILVER'
            
        selected = context.selected_objects
        if not selected:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
            
        for obj in selected:
            if obj.type != 'MESH':
                continue
                
            mat_name = f"Reflector_{material_type}"
            mat = bpy.data.materials.get(mat_name)
            
            # Create material if needed (reusing logic from add_reflector)
            if not mat:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                nodes.clear()
                
                node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                node_output = nodes.new(type='ShaderNodeOutputMaterial')
                mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
                
                if material_type == 'SILVER':
                    node_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
                    node_bsdf.inputs['Metallic'].default_value = 1.0
                    node_bsdf.inputs['Roughness'].default_value = 0.1
                elif material_type == 'GOLD':
                    node_bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.336, 1)
                    node_bsdf.inputs['Metallic'].default_value = 1.0
                    node_bsdf.inputs['Roughness'].default_value = 0.1
                elif material_type == 'WHITE':
                    node_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
                    node_bsdf.inputs['Metallic'].default_value = 0.0
                    node_bsdf.inputs['Roughness'].default_value = 0.5
                elif material_type == 'BLACK':
                    node_bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
                    node_bsdf.inputs['Metallic'].default_value = 0.0
                    node_bsdf.inputs['Roughness'].default_value = 1.0
            
            # Apply material
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
                
            # Ensure it is in the Reflectors collection
            ensure_collection_linked(context, obj, "Reflectors")
            
        self.report({'INFO'}, f"Applied {material_type} to selection")
        return {'FINISHED'}

class BLS_OT_import_custom_hdri(bpy.types.Operator):
    bl_idname = "bls.import_custom_hdri"
    bl_label = "Import Custom HDRI"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        
        # Load image
        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
        except:
            self.report({'ERROR'}, "Could not load image")
            return {'CANCELLED'}
            
        # Setup world (Using same logic as standard setup)
        world = context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            context.scene.world = world
        
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        
        node_output = nodes.new(type='ShaderNodeOutputWorld')
        node_bg = nodes.new(type='ShaderNodeBackground')
        node_env = nodes.new(type='ShaderNodeTexEnvironment')
        node_mapping = nodes.new(type='ShaderNodeMapping')
        node_coord = nodes.new(type='ShaderNodeTexCoord')
        
        node_env.image = img
        
        links.new(node_coord.outputs['Generated'], node_mapping.inputs['Vector'])
        links.new(node_mapping.outputs['Vector'], node_env.inputs['Vector'])
        links.new(node_env.outputs['Color'], node_bg.inputs['Color'])
        links.new(node_bg.outputs['Background'], node_output.inputs['Surface'])
        
        node_bg.name = "BLS_Background"
        node_mapping.name = "BLS_Mapping"
        
        props = context.scene.bls_props
        node_bg.inputs['Strength'].default_value = props.hdri_intensity
        node_mapping.inputs['Rotation'].default_value[2] = props.hdri_rotation * (3.14159 / 180.0)
        
        node_output.location = (400, 0)
        node_bg.location = (200, 0)
        node_env.location = (0, 0)
        node_mapping.location = (-200, 0)
        node_coord.location = (-400, 0)
        
        self.report({'INFO'}, f"Imported HDRI: {img.name}")
        return {'FINISHED'}
        
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class BLS_OT_import_custom_gobo(bpy.types.Operator):
    bl_idname = "bls.import_custom_gobo"
    bl_label = "Import Custom Texture"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
            
        light = context.active_object
        if not light or light.type != 'LIGHT':
            self.report({'ERROR'}, "Please select a light")
            return {'CANCELLED'}
            
        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
        except:
            self.report({'ERROR'}, "Could not load image")
            return {'CANCELLED'}
            
        light.data.use_nodes = True
        nodes = light.data.node_tree.nodes
        links = light.data.node_tree.links
        nodes.clear()
        
        node_emission = nodes.new(type='ShaderNodeEmission')
        node_output = nodes.new(type='ShaderNodeOutputLight')
        links.new(node_emission.outputs['Emission'], node_output.inputs['Surface'])
        
        node_tex = nodes.new(type='ShaderNodeTexImage')
        node_tex.image = img
        node_tex.location = (-300, 0)
        
        node_mapping = nodes.new(type='ShaderNodeMapping')
        node_mapping.location = (-500, 0)
        
        node_coord = nodes.new(type='ShaderNodeTexCoord')
        node_coord.location = (-700, 0)
        
        links.new(node_coord.outputs['UV'], node_mapping.inputs['Vector'])
        links.new(node_mapping.outputs['Vector'], node_tex.inputs['Vector'])
        links.new(node_tex.outputs['Color'], node_emission.inputs['Color'])
        
        # Ensure collection (Just in case)
        ensure_collection_linked(context, light, "Lights")
        
        self.report({'INFO'}, f"Applied Custom Texture: {img.name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class BLS_OT_import_custom_reflector(bpy.types.Operator):
    bl_idname = "bls.import_custom_reflector"
    bl_label = "Import Custom Reflector"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
            
        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
        except:
            self.report({'ERROR'}, "Could not load image")
            return {'CANCELLED'}
            
        # Create plane
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0))
        reflector = context.active_object
        reflector.name = f"Reflector_{img.name}"
        
        # Material
        mat = bpy.data.materials.new(name=f"Mat_{img.name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        # Principled BSDF with Image
        node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        node_tex = nodes.new(type='ShaderNodeTexImage')
        node_tex.image = img
        node_tex.location = (-300, 200)
        
        links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
        links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
        
        # Set Roughness to 1.0 (Matte) by default for custom images (Posters/etc)
        node_bsdf.inputs['Roughness'].default_value = 1.0
        node_bsdf.inputs['Metallic'].default_value = 0.0
        
        if reflector.data.materials:
            reflector.data.materials[0] = mat
        else:
            reflector.data.materials.append(mat)
            
        # Ensure collection
        ensure_collection_linked(context, reflector, "Reflectors")
        
        self.report({'INFO'}, f"Created Custom Reflector: {img.name}")
        return {'FINISHED'}
        
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

classes = (
    BLS_OT_setup_product_lighting,
    BLS_OT_setup_hdri,
    BLS_OT_add_reflector,
    BLS_OT_apply_reflector_material,
    BLS_OT_add_reflector_from_selection,
    BLS_OT_select_light,
    BLS_OT_auto_group_lights,
    BLS_OT_add_camera,
    BLS_OT_set_render_quality,
    BLS_OT_create_tracked_light,
    BLS_OT_create_camera_from_view,
    BLS_OT_set_gpu_render,
    BLS_OT_sync_camera_settings,
    BLS_OT_set_resolution,
    BLS_OT_create_cyclorama,
    BLS_OT_create_shadow_catcher,
    BLS_OT_import_custom_hdri,
    BLS_OT_import_custom_gobo,
    BLS_OT_import_custom_reflector,
    BLS_OT_import_custom_hdri,
    BLS_OT_import_custom_gobo,
    BLS_OT_import_custom_reflector,
    BLS_OT_import_custom_hdri,
    BLS_OT_import_custom_gobo,
    BLS_OT_import_custom_reflector,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            pass

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass