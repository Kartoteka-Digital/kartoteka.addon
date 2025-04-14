import bpy

def pivot_dropdown_items(self, context):
    return [
        ('pivot_bottom', 'Bottom', '-Z'),
        ('pivot_top', 'Top', '+Z'),
        ('pivot_left', 'Left', '-X'),
        ('pivot_right', 'Right', '+X'),
        ('pivot_front', 'Front', '-Y'),
        ('pivot_back', 'Back', '+Y'),
    ]

class VIEW3D_PT_helper_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kartoteka'
    bl_label = 'Kartoteka Helper'
    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene, "use_merge")
        row.operator("object.fast_apply", text="Fast Apply").merge = context.scene.use_merge

        layout.label(text=" ")
        col1 = layout.column(align=True, heading="Pivot Direction") 
        col1.prop(context.scene, "pivot_dropdown")
        col1.operator("object.place_pivot", text="Place Pivot").direction = context.scene.pivot_dropdown

        layout.label(text=" ")
        layout.operator("object.add_modifiers", text="Add Modifiers")

        layout.label(text=" ")
        layout.operator("object.new_group", text="Create New Group")

def add_pivot_dropdown(scene):
    if hasattr(scene, 'pivot_dropdown'):
        scene.pivot_dropdown = 'pivot_bottom'

def register():
    bpy.utils.register_class(VIEW3D_PT_helper_panel)
    bpy.types.Scene.use_merge = bpy.props.BoolProperty(name="Merge", default=True)
    bpy.types.Scene.pivot_dropdown = bpy.props.EnumProperty(
        name="Direction",
        description="Choose Pivot Direction",
        items=pivot_dropdown_items,
    )

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_helper_panel)
    del bpy.types.Scene.use_merge
    del bpy.types.Scene.pivot_dropdown