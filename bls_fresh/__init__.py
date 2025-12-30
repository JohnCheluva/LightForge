bl_info = {
    "name": "LightForge",
    "author": "Antigravity",
    "version": (1, 4, 22),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > LightForge",
    "description": "Professional Lighting and Rendering Tools",
    "warning": "",
    "doc_url": "",
    "category": "Lighting",
}

import bpy
import bpy.utils.previews
from . import ui
from . import operators
from . import gobos

modules = [
    gobos,
    operators,
    ui,
]

# Global preview collections
preview_collections = {}

def register():
    for module in modules:
        module.register()
    
    # Initialize preview collections
    pcoll_main = bpy.utils.previews.new()
    pcoll_hdri = bpy.utils.previews.new()
    pcoll_reflector = bpy.utils.previews.new()
    
    preview_collections["main"] = pcoll_main
    preview_collections["hdri"] = pcoll_hdri
    preview_collections["reflector"] = pcoll_reflector
    
    # Load icons
    gobos.load_gobo_icons(pcoll_main)
    gobos.load_hdri_icons(pcoll_hdri)
    gobos.load_reflector_icons(pcoll_reflector)
    
    print("BLS: Addon registered successfully")

def unregister():
    for module in reversed(modules):
        module.unregister()
    
    # Remove preview collections
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    print("BLS: Addon unregistered")

if __name__ == "__main__":
    register()