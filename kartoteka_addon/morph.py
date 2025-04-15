bl_info = {
    "name": "Coordinates",
    "author": "Demian",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Item Tab",
    "description": "Показывает координаты выбранных точек в режиме редактирования",
    "category": "Mesh",
}

import bpy
import bmesh

start_box = {
    "min-x": 0.0,
    "max-x": 0.0,
    "min-y": 0.0,
    "max-y": 0.0,
    "min-z": 0.0,
    "max-z": 0.0,
}

def calculate_multiplier(full_width, point):
    try:
        half_width = full_width / 2
        multiplier = abs(half_width / point)
        return multiplier
    except Exception as e:
        return f"Ошибка: {e}"
    
def calculate_difference(start, end):
    return end - start

class Multiplier_Operator(bpy.types.Operator):
    bl_idname = "object.calculate_multiplier"
    bl_label = "Calculate Multiplier"
    bl_options = {'REGISTER', 'UNDO'}

    value: bpy.props.FloatProperty()

    def execute(self, context):
        full_width = self.value

        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'WARNING'}, "Нет выделенных мешей")
            return {'CANCELLED'}
        
        obj = context.active_object

        bm = bmesh.from_edit_mesh(obj.data)
        active_verts = get_verts("act")
    
        if not active_verts:
            self.report({'WARNING'}, "Not active selected")
            return
        
        zero_count = get_zero_count()
        if zero_count == len(start_box):    
            self.report({'WARNING'}, "Calculate Start Box")
            return {'CANCELLED'}
        
        direction = context.scene.direction_dropdown
        finded = None
        axis = None

        if direction == "OPT_Top":
            finded = start_box['max-z']
            axis = 'z'
            target = full_width / 2
        elif direction == "OPT_Left":
            finded = start_box['min-x']
            axis = 'x'
            target = -full_width / 2
        elif direction == "OPT_Right":
            finded = start_box['max-x']
            axis = 'x'
            target = full_width / 2
        elif direction == "OPT_Front":
            finded = start_box['min-y']
            axis = 'y'
            target = -full_width / 2
        elif direction == "OPT_Back":
            finded = start_box['max-y']
            axis = 'y'
            target = full_width / 2
        else:
            self.report({'WARNING'}, "Направление не выбрано")
            return {'CANCELLED'}
        
        if context.scene.is_prop:
            multiplier = calculate_multiplier(full_width, finded)
            # self.report({'INFO'}, f"Multiplier: {multiplier}")
            for v in active_verts:
                if axis == 'x':
                    v.co.x *= multiplier
                elif axis == 'y':
                    v.co.y *= multiplier
                elif axis == 'z':
                    v.co.z *= multiplier
        else:
            difference = calculate_difference(finded, target)
            # self.report({'INFO'}, f"Difference: {difference}")
            for v in active_verts:
                if axis == 'x':
                    v.co.x += difference
                elif axis == 'y':
                    v.co.y += difference
                elif axis == 'z':
                    v.co.z += difference

        bmesh.update_edit_mesh(obj.data)
            
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}   

class Startbox_Operator(bpy.types.Operator):
    bl_idname = "object.calculate_startbox"
    bl_label = "Calculate Start Box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        unified_object = None
        duplicated_objects = None
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Choose Object Mode!")
            return {'CANCELLED'}
        
        if context.mode == 'OBJECT':
            selected_objects = context.selected_objects
            if not selected_objects:
                self.report({'WARNING'}, "No objects selected!")
                return {'CANCELLED'}
            
            empties = [obj for obj in selected_objects if obj.type == 'EMPTY']
            if empties:
                self.report({'WARNING'}, "Selected objects include Empty types!")
                return {'CANCELLED'}
            
            if selected_objects.__len__() > 1:
                bpy.ops.object.duplicate()
                duplicated_objects = context.selected_objects
            
            if duplicated_objects:
                context.view_layer.objects.active = duplicated_objects[0]
                bpy.ops.object.join()
                unified_object = context.view_layer.objects.active
                unified_object.name = "Joined Object"

        bpy.ops.object.mode_set(mode='EDIT')
        obj = context.active_object
    
        if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH':
            return

        # # Получаем bmesh для объекта в режиме редактирования
        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]
        
        if not selected_verts:
            return
        
        for v in bm.verts:
            v.select = True

        start_box['max-x'] = max(v.co.x for v in selected_verts)
        start_box['min-x'] = min(v.co.x for v in selected_verts)
        start_box['max-y'] = max(v.co.y for v in selected_verts)
        start_box['min-y'] = min(v.co.y for v in selected_verts)
        start_box['max-z'] = max(v.co.z for v in selected_verts)
        start_box['min-z'] = min(v.co.z for v in selected_verts)

        # self.report({'INFO'}, f"X: {start_box['min-x']}, {start_box['max-x']}")
        # self.report({'INFO'}, f"Y: {start_box['min-y']}, {start_box['max-y']}")
        # self.report({'INFO'}, f"Z: {start_box['min-z']}, {start_box['max-z']}")

        if unified_object:
            bpy.data.objects.remove(unified_object, do_unlink=True)

        return {'FINISHED'}    
    
def get_verts(variant):
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    for obj in selected_objects:
        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]

    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        active_verts = [v for v in bm.verts if v.select]

    if variant == "all":
        return list(set(selected_verts + active_verts))
    elif variant == "act":
        return active_verts
    elif variant == "sel":
        return selected_verts

def get_zero_count():
    zero_points = 0
    for start_point in start_box.values():
        if start_point == 0.0:
            zero_points += 1
    return zero_points

class VIEW3D_PT_COORDINATES(bpy.types.Panel):
    bl_label = "Kartoteka Morph"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kartoteka"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        if context.mode == 'OBJECT':
            layout.operator("object.calculate_startbox", text="Calculate Start Box")
            layout.label(text=" ")

        if context.mode == 'EDIT_MESH':
            zero_count = get_zero_count()
            if zero_count != len(start_box):
                selected_verts = get_verts("all")
                if selected_verts.__len__() == 0:
                    layout.label(text="Nothing selected")
                    return
                else:
                    cf = layout.column_flow(columns=2, align=True)
                    cf.prop(context.scene, "size")
                    cf.prop(context.scene, "is_prop")
                    layout.prop(context.scene, "direction_dropdown")

                    col2 = layout.column(align=True)
                    col2.operator("object.calculate_multiplier", text="Morph points").value = context.scene.size
            else:
                layout.label(text="Calculate Start Box in OBJECT mode")

def dropdown_items(self, context):
    return [
        ('OPT_Top', 'Top', '+Z'),
        ('OPT_Left', 'Left', '-X'),
        ('OPT_Right', 'Right', '+X'),
        ('OPT_Front', 'Front', '-Y'),
        ('OPT_Back', 'Back', '+Y'),
    ]

def print_selection(self, context):
    message = f"Вы выбрали 1: {self.direction_dropdown}"
    print(message)

class PANEL_OT_print_dropdown(bpy.types.Operator):
    bl_idname = "panel.print_dropdown"
    bl_label = "Print Selected Option"

    def execute(self, context):
        selected = context.scene.direction_dd
        self.report({'INFO'}, f"Вы выбрали: {selected}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(VIEW3D_PT_COORDINATES)
    bpy.utils.register_class(Multiplier_Operator)
    bpy.utils.register_class(Startbox_Operator)
    bpy.types.Scene.size = bpy.props.IntProperty(name="Full Width", default=10)
    bpy.types.Scene.is_prop = bpy.props.BoolProperty(name="Proportional", default=False)
    bpy.utils.register_class(PANEL_OT_print_dropdown)
    bpy.types.Scene.direction_dropdown = bpy.props.EnumProperty(
        name="Direction",
        description="dropdown menu",
        items=dropdown_items,
        update=lambda self, context: print_selection(self, context)
    )

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_COORDINATES)
    bpy.utils.unregister_class(Multiplier_Operator)
    bpy.utils.unregister_class(Startbox_Operator)
    del bpy.types.Scene.size
    del bpy.types.Scene.is_prop
    bpy.utils.unregister_class(PANEL_OT_print_dropdown)
    del bpy.types.Scene.direction_dropdown
