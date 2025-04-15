bl_info = {
    "name": "Kartoteka Addon",
    "author": "Demian, Nivis",
    "version": (1, 2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > UI > Kartoteka",
    "description": "Kartoteka Addon for Blender",
    "category": "Object",
}

import bpy
import json
import os
from . import (fast_apply, place_pivot, add_modifiers, new_group, helper_panel,
               operators, preview_panel,
               morph,
               prefs)

modules = [fast_apply, place_pivot, add_modifiers, new_group, helper_panel,
           operators, preview_panel,
           morph,
           prefs]

SAVE_FILE = os.path.join(os.path.expanduser("~"), "blender_render_settings.json")

def save_settings():
    settings = bpy.context.scene.render_settings
    data = {"save_path": settings.save_path}

    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
        print(f"[KARTOTEKA.PREVIEW] Настройки сохранены: {SAVE_FILE}")
    except Exception as e:
        print(f"[KARTOTEKA.PREVIEW] Ошибка сохранения настроек: {e}")

def load_settings():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
            bpy.context.scene.render_settings.save_path = data.get("save_path", "")
            print(f"[KARTOTEKA.PREVIEW] Настройки загружены: {SAVE_FILE}")
        except Exception as e:
            print(f"[KARTOTEKA.PREVIEW] Ошибка загрузки настроек: {e}")

@bpy.app.handlers.persistent
def load_post(dummy):
    load_settings()

def register():
    for module in modules:
        module.register()

    bpy.types.Scene.render_settings = bpy.props.PointerProperty(type=preview_panel.RenderSettings)

    bpy.app.handlers.load_post.append(load_post)

def unregister():
    save_settings()

    del bpy.types.Scene.render_settings

    for module in modules:
        module.unregister()

if __name__ == "__main__":
    register()