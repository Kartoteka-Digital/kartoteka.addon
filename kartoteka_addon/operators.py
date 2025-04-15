import bpy
from bpy.types import Operator
from bpy.props import StringProperty
import os
from .camera_utils import calculate_objects_bounds, setup_camera
from .compositing_manager import (
    setup_compositing_nodes_for_icon,
    setup_compositing_nodes_for_preview,
    setup_icon_settings,
    setup_preview_settings,
    setup_preview_settings_last_first_render
)


def move_selected_objects_to_collection(objs, collection_name="Collection"):
    """
    Перемещает все выделенные объекты в указанную коллекцию.
    Если объект имеет иерархию (дочерние объекты), переносит всю структуру.
    Если коллекция не существует, она создается.
    """
    scene = bpy.context.scene
    selected_objs = objs

    if not selected_objs:
        return

    if collection_name in bpy.data.collections:
        target_collection = bpy.data.collections[collection_name]
    else:
        target_collection = bpy.data.collections.new(collection_name)
        scene.collection.children.link(target_collection)

    def get_topmost_parent(obj):
        while obj.parent:
            obj = obj.parent
        return obj

    top_parents = {get_topmost_parent(obj) for obj in selected_objs}

    for parent in top_parents:
        if parent.name in target_collection.objects:
            continue

        for collection in parent.users_collection:
            collection.objects.unlink(parent)

        target_collection.objects.link(parent)


def find_topmost_parent(obj):
    """Находим самый верхний родитель, если объект находится в иерархии."""
    while obj.parent:
        obj = obj.parent
    return obj


def sanitize_filename(name, replacement='_'):
    """Убираем из имени недопустимые для файлов символы."""
    invalid_chars = r'\/:*?"<>|'
    for ch in invalid_chars:
        name = name.replace(ch, replacement)
    return name


def check_layer_exists(layer_name, operator=None):
    """
    Проверяет, существует ли слой с указанным именем.
    Если его нет, выводит ошибку в консоль и через self.report(), если оператор передан.
    """
    scene = bpy.context.scene
    if layer_name not in scene.view_layers:
        message = f"Ошибка: Слой '{layer_name}' не найден! Создайте его перед выполнением скрипта."
        print(message)  # Вывод в консоль Blender

        if operator:
            operator.report({'ERROR'}, message)

        return False
    return True


def save_project_if_unsaved():
    """
    Проверяет, сохранён ли текущий проект. Если нет — сохраняет его на рабочий стол.
    """
    if bpy.data.filepath:
        return

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    save_path = os.path.join(desktop_path, "kartoteka.view_project.blend")

    try:
        # Сохраняем файл
        bpy.ops.wm.save_as_mainfile(filepath=save_path)
        print(f" Проект сохранён в: {save_path}")
    except Exception as e:
        print(f" Ошибка при сохранении: {e}")


def delete_rendered_images():
    """
    Удаляет файлы 'object.png' и 'skybox.png' в директории, где сохранён .blend-файл.
    Если проект не сохранён, ничего не делает.
    """
    blend_file_path = bpy.data.filepath
    if not blend_file_path:
        return

    project_dir = os.path.dirname(blend_file_path)

    files_to_delete = ["object.png", "skybox.png"]

    for file_name in files_to_delete:
        file_path = os.path.join(project_dir, file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f" Ошибка при удалении {file_path}: {e}")
        else:
            print(f"ℹ Файл не найден (не требует удаления): {file_path}")


def create_new_layer():
    if "Skybox_Layer" not in bpy.context.scene.view_layers:
        # previous_view_layer = bpy.context.view_layer
        bpy.ops.scene.view_layer_add(type='EMPTY')
        bpy.context.view_layer.name = 'Skybox_Layer'

        # Restore the previous view layer since the operator changes the active view layer
        # bpy.context.window.view_layer = previous_view_layer

        for collection in bpy.context.scene.collection.children:
            bpy.context.window.view_layer.layer_collection.children[collection.name].exclude = True


class OBJECT_OT_RenderObjectPreview(Operator):
    bl_idname = "object.render_object_preview"
    bl_label = "Создать превью"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        save_project_if_unsaved()

        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objs:
            self.report({'WARNING'}, "Нет выделенных объектов!")
            return {'CANCELLED'}

        move_selected_objects_to_collection(selected_objs)
        center, size = calculate_objects_bounds(selected_objs)

        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "Нет активного объекта!")
            return {'CANCELLED'}

        create_new_layer()

        camera_position = scene.render_settings.camera_position
        camera_distance = scene.render_settings.camera_distance
        render_engine = scene.render_settings.render_engine
        compositing_blur = scene.render_settings.compositing_blur

        cam = setup_camera(
            scene=scene,
            center=center,
            size=size,
            side=camera_position,
            camera_dist=camera_distance,
            focus_obj=active_obj
        )
        scene.camera = cam
        scene.render.engine = render_engine

        scene.render.resolution_x = 512
        scene.render.resolution_y = 512

        if not check_layer_exists("ViewLayer") or not check_layer_exists("Skybox_Layer"):
            self.report({'ERROR'},
                        "Отсутствует один из слоёв: 'ViewLayer' или 'Skybox_Layer'. Создайте их перед запуском.")
            return {'CANCELLED'}

        setup_compositing_nodes_for_preview()
        setup_preview_settings(active_obj)
        setup_preview_settings_last_first_render(compositing_blur)

        top_parent = find_topmost_parent(active_obj)
        base_name = sanitize_filename(top_parent.name)

        save_directory = bpy.path.abspath(scene.render_settings.save_path)
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        output_path = os.path.join(save_directory, f"{base_name}_preview.jpg")

        bpy.data.images['Render Result'].save_render(filepath=output_path)

        self.report({'INFO'}, f"Иконка сохранена: {output_path}")

        delete_rendered_images()

        return {'FINISHED'}


class OBJECT_OT_RenderObjectIcon(Operator):
    """Создает иконку выделенного объекта (один рендер на ViewLayer)."""
    bl_idname = "object.render_object_icon"
    bl_label = "Создать иконку"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        save_project_if_unsaved()

        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objs:
            self.report({'WARNING'}, "Нет выделенных объектов!")
            return {'CANCELLED'}

        move_selected_objects_to_collection(selected_objs)
        center, size = calculate_objects_bounds(selected_objs)
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "Нет активного объекта!")
            return {'CANCELLED'}

        camera_position = scene.render_settings.camera_position
        render_engine = scene.render_settings.render_engine

        cam = setup_camera(
            scene=scene,
            center=center,
            size=size,
            side=camera_position,
            focus_obj=active_obj
        )
        scene.camera = cam
        scene.render.engine = render_engine

        scene.render.resolution_x = 384
        scene.render.resolution_y = 512

        setup_compositing_nodes_for_icon()
        setup_icon_settings(active_obj)

        top_parent = find_topmost_parent(active_obj)
        base_name = sanitize_filename(top_parent.name)

        save_directory = bpy.path.abspath(scene.render_settings.save_path)
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        output_path = os.path.join(save_directory, f"{base_name}_icon.png")

        bpy.data.images['Render Result'].save_render(filepath=output_path)

        self.report({'INFO'}, f"Иконка сохранена: {output_path}")

        delete_rendered_images()

        return {'FINISHED'}


class OBJECT_OT_SetSavePath(Operator):
    """Выбирает путь для сохранения рендеров"""
    bl_idname = "object.set_save_path"
    bl_label = "Выбрать путь сохранения"

    filepath: StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        context.scene.render_settings.save_path = self.filepath
        self.report({'INFO'}, f"Путь сохранения установлен: {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(OBJECT_OT_RenderObjectPreview)
    bpy.utils.register_class(OBJECT_OT_RenderObjectIcon)
    bpy.utils.register_class(OBJECT_OT_SetSavePath)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_RenderObjectPreview)
    bpy.utils.unregister_class(OBJECT_OT_RenderObjectIcon)
    bpy.utils.unregister_class(OBJECT_OT_SetSavePath)
