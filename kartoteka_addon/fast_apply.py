import bpy

class OBJECT_OT_fast_apply(bpy.types.Operator):
    """All Transforms -> Unlink -> Merge By Distance"""
    bl_idname = "object.fast_apply"
    bl_label = "Fast Apply"
    bl_options = {'REGISTER', 'UNDO'}
    
    merge: bpy.props.BoolProperty(name="Merge", default=True)

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Choose Object Mode!")
            return {'CANCELLED'}

        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        for obj in selected_objects:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        for obj in selected_objects:
            if obj.type == 'EMPTY':
                bpy.data.objects.remove(obj)

        if self.merge:
            # self.report({'INFO'}, f"Merge: {self.merge}")
            removed_vertices = 0
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles()
                    bpy.ops.object.mode_set(mode='OBJECT')
                    removed_vertices += len(obj.data.vertices)

            self.report({'INFO'}, f"Removed {removed_vertices} vertices")
            # self.report({'INFO'}, f"Merge: {self.merge}")
        
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OBJECT_OT_fast_apply)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_fast_apply)