import bpy
from bpy.types import Operator, Panel


class OBJECT_OT_split_by_materials(Operator):
    """Split selected meshes into separate objects by material slot"""
    bl_idname = "object.split_by_materials"
    bl_label = "Split by Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Choose Object Mode!")
            return {'CANCELLED'}

        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected!")
            return {'CANCELLED'}

        before = set(bpy.data.objects)
        processed = 0
        skipped = []

        for obj in meshes:
            if len(obj.data.materials) < 2:
                skipped.append(obj.name)
                continue

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='MATERIAL')
            bpy.ops.object.mode_set(mode='OBJECT')
            processed += 1

        new_objects = [o for o in bpy.data.objects if o not in before]
        for obj in new_objects:
            obj.select_set(True)

        msg = f"Split {processed} object(s) into {len(new_objects)} new piece(s)"
        if skipped:
            msg += f"; skipped (single material): {', '.join(skipped)}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class OBJECT_OT_rename_material(Operator):
    """Rename the single material of selected objects to a fixed tag"""
    bl_idname = "object.rename_material_tag"
    bl_label = "Rename Material"
    bl_options = {'REGISTER', 'UNDO'}

    target_name: bpy.props.StringProperty(default="tag_wall-outside")

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected!")
            return {'CANCELLED'}

        renamed = 0
        skipped = []
        for obj in meshes:
            slots = [s for s in obj.material_slots if s.material is not None]
            if len(slots) != 1:
                skipped.append(obj.name)
                continue
            slots[0].material.name = self.target_name
            renamed += 1

        msg = f"Renamed {renamed} material(s) to '{self.target_name}'"
        if skipped:
            msg += f"; skipped (not single material): {', '.join(skipped)}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class VIEW3D_PT_materials_panel(Panel):
    bl_label = "Materials on the Objects"
    bl_idname = "VIEW3D_PT_kartoteka_materials"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kartoteka"
    bl_order = 100

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.split_by_materials", text="Split by Materials", icon='MOD_EXPLODE')

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.uv_scale_to_meter", text="UV Scale 1m", icon='UV')

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.5
        op = row.operator("object.rename_material_tag", text="Rename for Tag", icon='MATERIAL')
        op.target_name = "tag_wall-outside"


classes = [
    OBJECT_OT_split_by_materials,
    OBJECT_OT_rename_material,
    VIEW3D_PT_materials_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
