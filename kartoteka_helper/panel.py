import bpy

class VIEW3D_PT_helper_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Helper'
    bl_label = 'Kartoteka Helper'
    
    def draw(self, context):
        layout = self.layout

        layout.operator("object.fast_apply", text="Fast Apply")
        layout.label(text=" ")
        layout.label(text="Place Pivot")
        row = layout.row(align=True)  # Выравнивание кнопок по горизонтали
        row.operator("object.place_pivot", text="Top").direction = "Top"
        row.operator("object.place_pivot", text="Bottom").direction = "Bottom"
        row.operator("object.place_pivot", text="Left").direction = "Left"
        row.operator("object.place_pivot", text="Right").direction = "Right"

        layout.label(text=" ")
        layout.operator("object.add_modifiers", text="Add Modifiers")

def register():
    bpy.utils.register_class(VIEW3D_PT_helper_panel)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_helper_panel)