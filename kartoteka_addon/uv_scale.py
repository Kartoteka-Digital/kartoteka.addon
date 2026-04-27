import bpy
import bmesh
from math import sqrt


_TARGET_SCALE = 0.5


class OBJECT_OT_uv_scale_to_meter(bpy.types.Operator):
    """Scale active UV map to match the standard 1 m² texture tile reference"""
    bl_idname = "object.uv_scale_to_meter"
    bl_label = "UV Scale 1m"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Choose Object Mode!")
            return {'CANCELLED'}

        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected!")
            return {'CANCELLED'}

        processed = 0
        skipped = []
        for obj in meshes:
            if self._scale_object_uv(obj):
                processed += 1
            else:
                skipped.append(obj.name)

        msg = f"UV scaled on {processed} object(s)"
        if skipped:
            msg += f"; skipped: {', '.join(skipped)}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def _scale_object_uv(self, obj):
        mesh = obj.data
        if not mesh.uv_layers.active or not mesh.polygons:
            return False

        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            uv_layer = bm.loops.layers.uv.active
            if uv_layer is None:
                return False

            mw = obj.matrix_world
            total_world_area = 0.0
            total_uv_area = 0.0
            cx = cy = 0.0
            loop_count = 0

            for face in bm.faces:
                verts_world = [mw @ v.co for v in face.verts]
                uvs = [loop[uv_layer].uv.copy() for loop in face.loops]
                if len(verts_world) < 3:
                    continue
                total_world_area += _poly_area_3d(verts_world)
                total_uv_area += _poly_area_2d(uvs)
                for uv in uvs:
                    cx += uv.x
                    cy += uv.y
                    loop_count += 1

            if total_uv_area <= 1e-12 or total_world_area <= 1e-12 or loop_count == 0:
                return False

            ratio = sqrt(total_world_area / total_uv_area) * _TARGET_SCALE
            cx /= loop_count
            cy /= loop_count

            for face in bm.faces:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    uv.x = cx + (uv.x - cx) * ratio
                    uv.y = cy + (uv.y - cy) * ratio

            bm.to_mesh(mesh)
            mesh.update()
            return True
        finally:
            bm.free()


def _poly_area_3d(pts):
    area = 0.0
    for i in range(1, len(pts) - 1):
        a = pts[i] - pts[0]
        b = pts[i + 1] - pts[0]
        area += a.cross(b).length * 0.5
    return area


def _poly_area_2d(pts):
    n = len(pts)
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def register():
    bpy.utils.register_class(OBJECT_OT_uv_scale_to_meter)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_uv_scale_to_meter)
