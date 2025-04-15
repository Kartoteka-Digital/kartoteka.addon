import bpy
from mathutils import Vector

class OBJECT_OT_new_group(bpy.types.Operator):
    bl_idname = "object.new_group"
    bl_label = "Create New Group"
    # bl_description = "Create a group of objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}
        
        empties = [obj for obj in selected_objects if obj.type == 'EMPTY']
        if empties:
            self.report({'WARNING'}, "Selected objects include Empty types!")
            return {'CANCELLED'}

        bpy.ops.object.empty_add()
        empty_group = context.active_object

        center = sum((obj.location for obj in selected_objects), Vector()) / len(selected_objects)
        empty_group.location = center
        
        for obj in selected_objects:
            obj.select_set(True)
        empty_group.select_set(True)
        context.view_layer.objects.active = empty_group
        bpy.ops.object.parent_set(type='OBJECT')

        empty_group.name = "New Group"

        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OBJECT_OT_new_group)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_new_group)