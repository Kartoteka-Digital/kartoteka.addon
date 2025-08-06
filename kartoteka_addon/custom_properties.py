import bpy
from bpy.types import Operator, Panel


class OBJECT_OT_add_custom_properties(Operator):
    """Add custom axis and limits properties to the selected object"""
    bl_idname = "object.add_custom_properties"
    bl_label = "Add Custom Properties"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        
        if obj is None:
            self.report({'WARNING'}, "No active object selected")
            return {'CANCELLED'}
        
        print(f"[DEBUG] Adding properties to object: {obj.name}")
        
        # Добавляем свойство "axis" (Integer Array) - [0, 1, 0]
        obj["axis"] = [0, 1, 0]
        
        # Настройка UI для axis
        try:
            ui = obj.id_properties_ui("axis")
            ui.update(
                default=(0, 1, 0),
                min=0,
                max=1,
                soft_min=0,
                soft_max=1,
                step=1,
                description=""
            )
            print("[DEBUG] axis UI settings applied")
        except Exception as e:
            print(f"[DEBUG] axis UI settings failed: {e}")
        
        # Добавляем свойство "limits" (Float Array) - [-90.0, 0.0]
        obj["limits"] = [-90.0, 0.0]
        
        # Настройка UI для limits
        try:
            ui = obj.id_properties_ui("limits")
            ui.update(
                default=(-90.0, 0.0),
                min=-360.0,
                max=360.0,
                soft_min=-360.0,
                soft_max=360.0,
                step=0.1,
                precision=3,
                description=""
            )
            print("[DEBUG] limits UI settings applied")
        except Exception as e:
            print(f"[DEBUG] limits UI settings failed: {e}")
        
        # Проверяем, что свойства созданы
        if "axis" in obj and "limits" in obj:
            self.report({'INFO'}, f"Custom properties added to {obj.name}")
            print(f"[DEBUG] Properties created - axis: {obj['axis']}, limits: {obj['limits']}")
        else:
            self.report({'ERROR'}, "Failed to create properties")
            print("[DEBUG] Failed to create properties")
            
        return {'FINISHED'}


class VIEW3D_PT_custom_properties_button(Panel):
    """Simple panel with just a button to add custom properties"""
    bl_label = "Custom Properties"
    bl_idname = "VIEW3D_PT_kartoteka_custom_properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kartoteka"

    def draw(self, context):
        layout = self.layout
        
        # Только кнопка для добавления свойств
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.add_custom_properties", text="Add Custom Properties", icon='ADD')


classes = [
    OBJECT_OT_add_custom_properties,
    VIEW3D_PT_custom_properties_button,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)