import bpy
import mathutils

class OBJECT_OT_add_modifiers(bpy.types.Operator):
    """Decimate Collapse, Decimate Planar, Weighted Normals"""
    bl_idname = "object.add_modifiers"
    bl_label = "Add Modifiers"
    
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':  # Добавляем модификаторы только для объектов типа 'MESH'
                # Добавляем модификатор Decimate Collapse
                decimate_collapse = obj.modifiers.new(name="Decimate Collapse", type='DECIMATE')
                decimate_collapse.decimate_type = 'COLLAPSE'
                decimate_collapse.show_viewport = True
                
                # Добавляем модификатор Decimate Planar
                decimate_planar = obj.modifiers.new(name="Decimate Planar", type='DECIMATE')
                decimate_planar.decimate_type = 'DISSOLVE'
                decimate_planar.show_viewport = False
                
                # Добавляем модификатор Weighted Normals
                weighted_normals = obj.modifiers.new(name="Weighted Normals", type='WEIGHTED_NORMAL')
                weighted_normals.show_viewport = False

        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OBJECT_OT_add_modifiers)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_modifiers)