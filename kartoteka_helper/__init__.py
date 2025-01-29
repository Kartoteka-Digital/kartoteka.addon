bl_info = {
    "name": "Kartoteka Helper",
    "author": "Demian",
    "version": (0, 4),
    "blender": (3, 0, 0),
    "location": "View3D > UI > Helper",
    "description": "Kartoteka Helper for Blender",
    "category": "Object",
}

import bpy
from . import fast_apply, place_pivot, add_modifiers, panel

modules = [fast_apply, place_pivot, add_modifiers, panel]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in modules:
        module.unregister()

if __name__ == "__main__":
    register()