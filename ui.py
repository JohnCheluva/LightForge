import bpy

class BLS_PT_SetupPanel(bpy.types.Panel):
    bl_label = "Scene Setup"
    bl_idname = "BLS_PT_setup_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LightForge"
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='SCENE_DATA')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.bls_props
        
        # --- Section Title ---
        box = layout.box()
        box.alert = True # Coloured Highlight
        box.label(text="Lighting Tools", icon='SCENE_DATA')
        
        # Light creation buttons
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("bls.setup_product_lighting", text="3 Point Lighting", icon='LIGHT_AREA')
        col.operator("bls.create_tracked_light", text="Create Light", icon='LIGHT_SPOT')
        
        col.separator()
        # Moved Studio Tools here
        col.operator("bls.create_cyclorama", text="Create Studio Backdrop", icon='MESH_CUBE')
        col.operator("bls.create_shadow_catcher", text="Shadow Catcher", icon='IMAGE_ALPHA')
        
        layout.separator()
        
        # HDRI Library
        box = layout.box()
        box.label(text="HDRI Library", icon='WORLD')
        row = box.row()
        if props.active_hdri_texture == "NONE":
            box.label(text="No HDRIs found", icon='ERROR')
            box.label(text="Place HDRIs in textures/hdri folder", icon='INFO')
        else:
            row.template_icon_view(props, "active_hdri_texture", show_labels=True)
            
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator("bls.apply_hdri_from_lib", text="Apply HDRI", icon='WORLD')
        row.operator("bls.import_custom_hdri", text="", icon='FILE_FOLDER')
        row.operator("bls.reload_icons", text="", icon='FILE_REFRESH')
        
        if props.active_hdri_texture != "NONE":
            col = box.column(align=True)
            col.prop(props, "hdri_intensity", text="Intensity")
            col.prop(props, "hdri_rotation", text="Rotation")
        
        layout.separator()
        layout.operator("bls.debug_info", text="Debug Info", icon='CONSOLE')

class BLS_PT_TexturePanel(bpy.types.Panel):
    bl_label = "Light Texturing"
    bl_idname = "BLS_PT_texture_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LightForge"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='TEXTURE')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.bls_props
        
        row = layout.row()
        row.prop(props, "texture_type", expand=True)
        
        layout.separator()
        
        if props.texture_type == 'IMAGE':
            if props.active_gobo_texture == "NONE":
                layout.label(text="No textures found!", icon='ERROR')
                layout.operator("bls.generate_defaults", text="Generate Defaults", icon='FILE_NEW')
            else:
                layout.template_icon_view(props, "active_gobo_texture", show_labels=False)
            
            row = layout.row(align=True)
            row.scale_y = 1.3
            row.operator("bls.apply_gobo", text="Apply to Selected", icon='CHECKMARK')
            row.operator("bls.import_custom_gobo", text="", icon='FILE_FOLDER')
            row.operator("bls.reload_icons", text="", icon='FILE_REFRESH')
            
            # Camera Visibility (Moved here)
            layout.prop(props, "gobo_camera_visible", text="Camera Visibility")
            
        elif props.texture_type == 'PROCEDURAL':
            row = layout.row()
            row.prop(props, "procedural_type", expand=True)
            
            row = layout.row()
            row.scale_y = 1.3
            if props.procedural_type == 'GRADIENT':
                row.operator("bls.apply_gobo", text="Apply Gradient", icon='IPO_LINEAR')
            else:
                row.operator("bls.apply_gobo", text="Apply Noise", icon='MOD_NOISE')
            
            # Camera Visibility for Procedural
            layout.prop(props, "gobo_camera_visible", text="Camera Visibility")

class BLS_PT_ReflectorPanel(bpy.types.Panel):
    bl_label = "Reflector Generator"
    bl_idname = "BLS_PT_reflector_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LightForge"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='MESH_PLANE')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.bls_props
        
        layout.template_icon_view(props, "active_reflector", show_labels=True)
        
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("bls.add_reflector_from_selection", text="Add Reflector", icon='CHECKMARK')
        row.operator("bls.apply_reflector_material", text="Apply to Selected", icon='BRUSH_DATA')
        row.operator("bls.import_custom_reflector", text="", icon='FILE_FOLDER')
        row.operator("bls.reload_icons", text="", icon='FILE_REFRESH')

class BLS_PT_MixerPanel(bpy.types.Panel):
    bl_label = "Light Mixer"
    bl_idname = "BLS_PT_mixer_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LightForge"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='LIGHT_DATA')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.operator("bls.auto_group_lights", text="Auto Group Lights", icon='GROUP')
        layout.separator()
        
        col = layout.column(align=True)
        for obj in scene.objects:
            if obj.type == 'LIGHT':
                box = col.box()
                row = box.row(align=True)
                op = row.operator("bls.select_light", text="", icon='RESTRICT_SELECT_OFF' if obj == context.active_object else 'RESTRICT_SELECT_ON')
                op.light_name = obj.name
                row.prop(obj, "name", text="")
                row.prop(obj, "hide_viewport", text="", icon='HIDE_OFF' if not obj.hide_viewport else 'HIDE_ON')
                row.prop(obj, "hide_render", text="", icon='RESTRICT_RENDER_OFF' if not obj.hide_render else 'RESTRICT_RENDER_ON')
                
                sub = box.row(align=True)
                sub.prop(obj.data, "color", text="")
                sub.prop(obj.data, "energy", text="Power")
                if hasattr(obj.data, "spread"):
                    sub.prop(obj.data, "spread", text="Spread")

class BLS_PT_CameraPanel(bpy.types.Panel):
    bl_label = "Camera Manager"
    bl_idname = "BLS_PT_camera_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LightForge"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='CAMERA_DATA')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.bls_props
        
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("bls.create_camera_from_view", text="Camera from View", icon='VIEW_CAMERA')
        
        row = layout.row(align=True)
        row.operator("bls.add_camera", text="35mm").focal_length = 35
        row.operator("bls.add_camera", text="50mm").focal_length = 50
        row.operator("bls.add_camera", text="85mm").focal_length = 85
        
        cam = scene.camera
        if cam and cam.type == 'CAMERA':
            box = layout.box()
            box.label(text=f"Active: {cam.name}", icon='CAMERA_DATA')
            
            col = box.column(align=True)
            col.prop(cam.data, "lens", text="Focal Length")
            col.prop(cam.data, "sensor_width", text="Sensor Size")
            
            layout.separator()
            box = layout.box()
            box.prop(props, "dof_active", text="Depth of Field", icon='HIDE_OFF' if props.dof_active else 'HIDE_ON')
            if props.dof_active:
                box.prop(props, "dof_target", text="Focus Object")
                # Show F-stop and distance (RESTORED)
                col = box.column(align=True)
                col.prop(cam.data.dof, "aperture_fstop", text="F-Stop")
                if not props.dof_target:
                    col.prop(cam.data.dof, "focus_distance", text="Focus Distance")
            
            layout.separator()
            box = layout.box()
            box.label(text="Display & Performance", icon='VIS_SEL_11')
            box.prop(cam.data, "passepartout_alpha", text="Passepartout", slider=True)
            box.prop(props, "use_motion_blur", text="Motion Blur")
            
            layout.separator()
            layout.operator("bls.sync_camera_settings", text="Sync to Camera", icon='FILE_TICK')

class BLS_PT_RenderPanel(bpy.types.Panel):
    bl_label = "Render & Output"
    bl_idname = "BLS_PT_render_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LightForge"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='RENDER_RESULT')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.bls_props
        
        # GPU / Device (HIGHLIGHTED)
        box = layout.box()
        box.alert = True # Coloured Highlight
        box.label(text="Hardware Acceleration", icon='NODE_COMPOSITING')
        box.prop(props, "gpu_device", text="Mode")
        
        # Quality Presets (HIGHLIGHTED)
        layout.separator()
        box = layout.box()
        box.label(text="Render Quality", icon='RENDER_RESULT')
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator("bls.set_render_quality", text="Draft").quality = 'DRAFT'
        row.operator("bls.set_render_quality", text="Medium").quality = 'MEDIUM'
        row.operator("bls.set_render_quality", text="High").quality = 'HIGH'
        row.operator("bls.set_render_quality", text="Ultra").quality = 'ULTRA'
        
        # Resolution Presets
        layout.separator()
        layout.label(text="Resolution Manager", icon='IMAGE_DATA')
        grid = layout.grid_flow(columns=2, align=True)
        
        op = grid.operator("bls.set_resolution", text="4K Ultra", icon='IMAGE_DATA')
        op.res_x = 3840
        op.res_y = 2160
        
        op = grid.operator("bls.set_resolution", text="1080p HD", icon='IMAGE_DATA')
        op.res_x = 1920
        op.res_y = 1080
        
        op = grid.operator("bls.set_resolution", text="Portrait", icon='ORIENTATION_VIEW')
        op.res_x = 1080
        op.res_y = 1920
        
        op = grid.operator("bls.set_resolution", text="Square", icon='UV_DATA')
        op.res_x = 1080
        op.res_y = 1080
        
        # Custom Resolution
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene.render, "resolution_x", text="Width")
        col.prop(scene.render, "resolution_y", text="Height")
        col.prop(scene.render, "resolution_percentage", text="%")
        
        # Features
        layout.separator()
        layout.prop(scene.render, "film_transparent", text="Transparent BG")
        
        if scene.render.engine == 'CYCLES':
            # Samples (RESTORED)
            box = layout.box()
            box.label(text="Sampling", icon='RENDER_STILL')
            col = box.column(align=True)
            col.prop(scene.cycles, "samples", text="Render Samples")
            col.prop(scene.cycles, "preview_samples", text="Viewport Samples")
            col.prop(scene.cycles, "use_denoising", text="Use Denoising")
            
            # Performance
            box = layout.box()
            box.label(text="Performance", icon='MEMORY')
            col = box.column(align=True)
            col.prop(scene.render, "use_persistent_data", text="Persistent Data")
            if hasattr(scene.cycles, 'use_auto_tile'):
                col.prop(scene.cycles, "use_auto_tile", text="Use Tiling")
            if hasattr(scene.cycles, 'tile_size'):
                col.prop(scene.cycles, "tile_size", text="Tile Size")
            
            # Fast GI Approximation
            layout.separator()
            box = layout.box()
            box.label(text="Fast GI (Speed Up)", icon='LIGHT_SUN')
            if hasattr(scene.cycles, 'use_fast_gi'):
                box.prop(scene.cycles, "use_fast_gi", text="Enable Fast GI")
            if hasattr(scene.cycles, 'ao_bounces'):
                box.prop(scene.cycles, "ao_bounces", text="Viewport Bounces")
                box.prop(scene.cycles, "ao_bounces_render", text="Render Bounces")
        
        # Color Management
        box = layout.box()
        box.label(text="Color Grading", icon='COLORSET_01_VEC')
        col = box.column(align=True)
        col.prop(scene.view_settings, "view_transform", text="Transform")
        col.prop(scene.view_settings, "look", text="Look")
        col.prop(scene.view_settings, "exposure", text="Exposure")
        col.prop(scene.view_settings, "gamma", text="Gamma")

classes = (
    BLS_PT_SetupPanel,
    BLS_PT_TexturePanel,
    BLS_PT_ReflectorPanel,
    BLS_PT_MixerPanel,
    BLS_PT_CameraPanel,
    BLS_PT_RenderPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)