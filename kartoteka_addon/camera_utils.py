import bpy
import math
import mathutils


def calculate_objects_bounds(objects):
    all_coords = []
    for obj in objects:
        # Берём координаты bound_box в мировых координатах
        bbox_coords = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        all_coords.extend(bbox_coords)

    if not all_coords:
        return mathutils.Vector((0, 0, 0)), 0

    x_min = min(v.x for v in all_coords)
    x_max = max(v.x for v in all_coords)
    y_min = min(v.y for v in all_coords)
    y_max = max(v.y for v in all_coords)
    z_min = min(v.z for v in all_coords)
    z_max = max(v.z for v in all_coords)

    center = mathutils.Vector((
        (x_min + x_max) / 2.0,
        (y_min + y_max) / 2.0,
        (z_min + z_max) / 2.0
    ))
    size = max(x_max - x_min, y_max - y_min, z_max - z_min)
    return center, size


def look_at(cam_obj, target):
    direction = (target - cam_obj.location).normalized()
    inv_dir = -direction
    quat = inv_dir.to_track_quat('Z', 'Y')
    cam_obj.rotation_euler = quat.to_euler()


def setup_camera(scene, center, size, side='GENERAL', camera_dist=2.5, focus_obj=None):
    # Удаляем старую камеру Preview_Camera, если есть
    for o in bpy.data.objects:
        if o.type == 'CAMERA' and o.name.startswith("Preview_Camera"):
            bpy.data.objects.remove(o, do_unlink=True)

    # Создаём новую камеру
    cam_data = bpy.data.cameras.new("Preview_Camera")
    cam_obj = bpy.data.objects.new("Preview_Camera", cam_data)
    scene.collection.objects.link(cam_obj)

    # Рассчитываем расстояние, с которого будем смотреть на bounding box
    dist = size * camera_dist

    # Выбираем угол в зависимости от параметра side
    if side == 'LEFT':
        angle_deg = 230.0
    elif side == 'RIGHT':
        angle_deg = -50.0
    else:  # GENERAL
        angle_deg = -90.0

    angle_rad = math.radians(angle_deg)
    cam_x = center.x + dist * math.cos(angle_rad)
    cam_y = center.y + dist * math.sin(angle_rad)
    cam_z = center.z + size * 0.3

    cam_obj.location = mathutils.Vector((cam_x, cam_y, cam_z))

    # Поворачиваем камеру, чтобы –Z смотрел на центр
    look_at(cam_obj, center)

    # Настраиваем DOF
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = focus_obj  # Если хотим фокусироваться на активном объекте

    # Делаем камеру активной
    scene.camera = cam_obj
    return cam_obj
