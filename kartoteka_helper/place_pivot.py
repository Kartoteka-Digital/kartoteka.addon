import bpy
import mathutils

class OBJECT_OT_place_pivot(bpy.types.Operator):
    bl_idname = "object.place_pivot"
    bl_label = "Place Pivot"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.StringProperty()
    
    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Choose Object Mode!")
            return {'CANCELLED'}

        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}
        
        empties = [obj for obj in selected_objects if obj.type == 'EMPTY']
        if empties:
            self.report({'WARNING'}, "Selected objects include Empty types!")
            return {'CANCELLED'}
        
        bpy.ops.object.duplicate()
        duplicated_objects = bpy.context.selected_objects
        
        if duplicated_objects:
            context.view_layer.objects.active = duplicated_objects[0]
            bpy.ops.object.join()
            unified_object = context.view_layer.objects.active
            unified_object.name = "Joined Object"
            self.set_origin_point(unified_object, context)

            for obj in selected_objects:
                obj.select_set(True)
            unified_object.select_set(True)
            bpy.ops.object.parent_set(type='OBJECT')

            for obj in selected_objects:
                obj.select_set(False)
                
            cursor_location = bpy.context.scene.cursor.location
            delta = cursor_location - unified_object.location
            unified_object.location += delta

            unified_object.select_set(False)
            for obj in selected_objects:
                obj.select_set(True)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

            unified_object.select_set(True)
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.data.objects.remove(unified_object, do_unlink=True)
                    
        return {'FINISHED'}
    
    def set_origin_point(self, obj, context):
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        new_origin = (0, 0, 0)

        if self.direction in ["Top", "Bottom"]:
            point_z = max(corner.z for corner in bbox_corners) if self.direction == "Top" else min(corner.z for corner in bbox_corners)
            center_x = sum(corner.x for corner in bbox_corners) / 8
            center_y = sum(corner.y for corner in bbox_corners) / 8
            new_origin = mathutils.Vector((center_x, center_y, point_z))
        
        elif self.direction in ["Left", "Right"]:
            point_x = min(corner.x for corner in bbox_corners) if self.direction == "Left" else max(corner.x for corner in bbox_corners)
            center_y = sum(corner.y for corner in bbox_corners) / 8
            center_z = sum(corner.z for corner in bbox_corners) / 8
            new_origin = mathutils.Vector((point_x, center_y, center_z))
        
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
        context.scene.cursor.location = new_origin
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
        context.scene.cursor.location = (0, 0, 0)

def register():
    bpy.utils.register_class(OBJECT_OT_place_pivot)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_place_pivot)