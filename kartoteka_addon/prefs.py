import bpy

def update_statistics_visibility(self, context):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_stats = self.show_statistics

class AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = "kartoteka_addon"

    show_statistics: bpy.props.BoolProperty(
        name="Statistics",
        description="Show Viewport Statistics Overlay",
        default=False,
        update=update_statistics_visibility
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "show_statistics")

def register():
    bpy.utils.register_class(AddonPrefs)

    prefs = bpy.context.preferences.addons["kartoteka_addon"].preferences
    update_statistics_visibility(prefs, bpy.context)

def unregister():
    bpy.utils.unregister_class(AddonPrefs)
