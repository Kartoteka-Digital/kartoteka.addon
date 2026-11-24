import bpy
import bmesh
from math import log2

SMALL_TRIS = 500
DRAW_CALL_LIMIT = 100


def _is_pot(n):
    return n > 0 and (n & (n - 1)) == 0


def nearest_pot(n):
    """Nearest power of two; values from about the middle of the range upward round up."""
    if n <= 1:
        return 1
    lo = 2 ** int(log2(n))
    if lo == n:
        return n
    hi = lo * 2
    return lo if n - lo < (hi - n) * 0.75 else hi


def _pot_items(n):
    near = nearest_pot(n)
    sizes = sorted({max(16, near // 4), max(16, near // 2), near, near * 2} | {2 ** int(log2(max(n, 1))), 2 ** (int(log2(max(n, 1))) + 1)})
    return [(str(s), f"{s}" + ("  (nearest)" if s == near else ""), "") for s in sizes if s <= 8192]


def _scope_objects(context):
    sel = [o for o in context.selected_objects if o.type == 'MESH']
    return sel or [o for o in context.scene.objects if o.type == 'MESH' and o.visible_get()]


def _tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def _images(objs):
    imgs = {}
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.use_nodes:
                continue
            for node in m.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image and node.image.size[0] > 0:
                    imgs.setdefault(node.image.name, (node.image, set()))[1].add(m.name)
    return imgs


def _quest_mb(img):
    w, h = img.size
    alpha = img.alpha_mode != 'NONE' and img.depth in (32, 64, 128)
    if _is_pot(w) and _is_pot(h):
        return w * h * (1 if alpha else 0.5) * 4 / 3 / 1048576
    return (w * h * 4 * 4 / 3 + w * h * 4) / 1048576


def analyze(context):
    objs = _scope_objects(context)
    by_mat = {}
    draw_calls = small = tris = 0
    for o in objs:
        t = _tris(o)
        tris += t
        mats = [s.material.name if s.material else "—" for s in o.material_slots] or ["—"]
        draw_calls += len(mats)
        if t < SMALL_TRIS:
            small += 1
        if len(set(mats)) == 1:
            e = by_mat.setdefault(mats[0], [0, 0])
            e[0] += 1
            if t < SMALL_TRIS:
                e[1] += 1
    imgs = _images(objs)
    npot = [(img, mats) for img, mats in imgs.values() if not (_is_pot(img.size[0]) and _is_pot(img.size[1]))]
    return {
        "objects": len(objs), "draw_calls": draw_calls, "small": small, "tris": tris,
        "split": sorted(((m, c, s) for m, (c, s) in by_mat.items() if c >= 2), key=lambda x: -x[1]),
        "tex_mb": sum(_quest_mb(i) for i, _ in imgs.values()), "tex_count": len(imgs),
        "npot": sorted(npot, key=lambda x: -_quest_mb(x[0])),
    }


class OBJECT_OT_kq_merge_by_material(bpy.types.Operator):
    """Join mesh objects that use the same single material into one object per material — fewer draw calls on Quest"""
    bl_idname = "object.kq_merge_by_material"
    bl_label = "Merge by Material"
    bl_options = {'REGISTER', 'UNDO'}

    material: bpy.props.StringProperty(default="", description="Only this material (empty — all)")

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Choose Object Mode!")
            return {'CANCELLED'}
        groups = {}
        for o in _scope_objects(context):
            mats = {s.material.name for s in o.material_slots if s.material}
            if len(mats) == 1 and len(o.material_slots) >= 1 and not o.data.shape_keys and o.data.users == 1:
                name = mats.pop()
                if not self.material or name == self.material:
                    groups.setdefault(name, []).append(o)
        merged = 0
        for name, objs in groups.items():
            if len(objs) < 2:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            for o in objs:
                o.select_set(True)
            context.view_layer.objects.active = objs[0]
            bpy.ops.object.join()
            objs[0].name = name
            merged += len(objs) - 1
        self.report({'INFO'}, f"Merged {merged} object(s)")
        return {'FINISHED'}


class OBJECT_OT_kq_select_by_material(bpy.types.Operator):
    """Select objects that use this material (or this image when an image is given)"""
    bl_idname = "object.kq_select_by"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'}

    material: bpy.props.StringProperty(default="")
    image: bpy.props.StringProperty(default="")

    def execute(self, context):
        objs = []
        for o in context.view_layer.objects:
            if o.type != 'MESH':
                continue
            for slot in o.material_slots:
                m = slot.material
                if not m:
                    continue
                if self.material and m.name == self.material:
                    objs.append(o)
                    break
                if self.image and m.use_nodes and any(n.type == 'TEX_IMAGE' and n.image and n.image.name == self.image for n in m.node_tree.nodes):
                    objs.append(o)
                    break
        if not objs:
            return {'CANCELLED'}
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        context.view_layer.objects.active = objs[0]
        self.report({'INFO'}, f"Selected {len(objs)} object(s)")
        return {'FINISHED'}


class IMAGE_OT_kq_resize_pot(bpy.types.Operator):
    """Resize the image to power-of-two sides so it gets compressed on Quest. UVs and tiling stay the same; the result is packed into the .blend"""
    bl_idname = "image.kq_resize_pot"
    bl_label = "Resize to Power of Two"
    bl_options = {'REGISTER', 'UNDO'}

    image: bpy.props.StringProperty()
    width: bpy.props.EnumProperty(name="Width", items=lambda self, ctx: _pot_items(bpy.data.images[self.image].size[0]) if self.image in bpy.data.images else [("1024", "1024", "")])
    height: bpy.props.EnumProperty(name="Height", items=lambda self, ctx: _pot_items(bpy.data.images[self.image].size[1]) if self.image in bpy.data.images else [("1024", "1024", "")])

    def invoke(self, context, event):
        img = bpy.data.images.get(self.image)
        if not img:
            return {'CANCELLED'}
        self.width = str(nearest_pot(img.size[0]))
        self.height = str(nearest_pot(img.size[1]))
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        img = bpy.data.images.get(self.image)
        col = self.layout.column()
        if img:
            col.label(text=f"{img.name}: {img.size[0]}×{img.size[1]}")
        col.prop(self, "width")
        col.prop(self, "height")

    def execute(self, context):
        img = bpy.data.images.get(self.image)
        if not img:
            return {'CANCELLED'}
        _resize(img, int(self.width), int(self.height))
        self.report({'INFO'}, f"{img.name} → {self.width}×{self.height}")
        return {'FINISHED'}


class IMAGE_OT_kq_resize_all_pot(bpy.types.Operator):
    """Resize every non power-of-two image used by the selected objects to the nearest power of two"""
    bl_idname = "image.kq_resize_all_pot"
    bl_label = "Resize All to Nearest"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        npot = analyze(context)["npot"]
        for img, _ in npot:
            _resize(img, nearest_pot(img.size[0]), nearest_pot(img.size[1]))
        self.report({'INFO'}, f"Resized {len(npot)} image(s)")
        return {'FINISHED'}


def _resize(img, w, h):
    img.scale(w, h)
    img.pack()


class VIEW3D_PT_kartoteka_quest_check(bpy.types.Panel):
    bl_label = "Quest Check"
    bl_idname = "VIEW3D_PT_kartoteka_quest_check"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kartoteka"
    bl_order = 101
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        if context.mode != 'OBJECT':
            layout.label(text="Object Mode only", icon='INFO')
            return
        r = analyze(context)
        scope = "selected" if any(o.type == 'MESH' for o in context.selected_objects) else "scene"

        box = layout.box()
        box.label(text=f"{r['objects']} objects ({scope}) · {r['tris']:,} tris".replace(",", " "))
        dc = box.row()
        dc.alert = r["draw_calls"] > DRAW_CALL_LIMIT
        dc.label(text=f"Draw calls: {r['draw_calls']}" + (f" — aim for ≤{DRAW_CALL_LIMIT}" if dc.alert else ""), icon='ERROR' if dc.alert else 'CHECKMARK')
        box.label(text=f"Small objects (<{SMALL_TRIS} tris): {r['small']}")
        box.label(text=f"Textures on Quest: {r['tex_count']} · ~{r['tex_mb']:.1f} MB")

        if r["split"]:
            box = layout.box()
            box.label(text="Same material, separate objects", icon='MOD_EXPLODE')
            for name, count, small in r["split"][:8]:
                row = box.row(align=True)
                sel = row.operator("object.kq_select_by", text=f"{name}: {count} obj" + (f" ({small} small)" if small else ""), emboss=False, icon='RESTRICT_SELECT_OFF')
                sel.material = name
                op = row.operator("object.kq_merge_by_material", text="", icon='AUTOMERGE_ON')
                op.material = name
            row = box.row()
            row.scale_y = 1.3
            row.operator("object.kq_merge_by_material", text="Merge All by Material", icon='AUTOMERGE_ON').material = ""

        if r["npot"]:
            box = layout.box()
            box.alert = True
            box.label(text="Not power of two", icon='ERROR')
            box.label(text="not compressed on Quest")
            for img, mats in r["npot"][:12]:
                w, h = img.size
                col = box.column(align=True)
                row = col.row(align=True)
                row.alert = False
                sel = row.operator("object.kq_select_by", text=img.name, emboss=False, icon='IMAGE_DATA')
                sel.image = img.name
                op = row.operator("image.kq_resize_pot", text="", icon='FULLSCREEN_ENTER')
                op.image = img.name
                info = col.row()
                info.alert = True
                info.label(text=f"{w}×{h}  →  {nearest_pot(w)}×{nearest_pot(h)}")
                info2 = info.row()
                info2.alert = False
                info2.alignment = 'RIGHT'
                info2.label(text=f"{_quest_mb(img):.1f} MB")
            row = box.row()
            row.alert = False
            row.scale_y = 1.3
            row.operator("image.kq_resize_all_pot", text="Resize All to Nearest", icon='IMAGE_DATA')


classes = (OBJECT_OT_kq_merge_by_material, OBJECT_OT_kq_select_by_material, IMAGE_OT_kq_resize_pot, IMAGE_OT_kq_resize_all_pot, VIEW3D_PT_kartoteka_quest_check)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
