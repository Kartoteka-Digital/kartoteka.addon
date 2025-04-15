import bpy
import os
import math

from .node_utils import (
    get_or_create_node,
    ensure_link
)


def get_addon_dir():
    return os.path.dirname(__file__)


def get_assets_dir():
    return os.path.join(get_addon_dir(), "assets")


def list_skybox_files():
    """
    Ищет в папке 'assets' файлы с расширениями HDR/EXR/PNG/JPG/JPEG
    и формирует список для EnumProperty.
    """
    path = get_assets_dir()
    if not os.path.isdir(path):
        print(f"[Skybox] Не найдена папка: {path}")
        return []

    items = []
    for fname in os.listdir(path):
        ext = os.path.splitext(fname)[1].lower()
        if ext in (".hdr", ".exr", ".png", ".jpg", ".jpeg"):
            items.append((fname, fname, f"Использовать {fname} в качестве скайбокса"))
    items.sort(key=lambda x: x[0].lower())
    return items


def delete_all_world_nodes():
    scene = bpy.context.scene
    if not scene or not scene.world:
        return

    world = scene.world
    if not world.use_nodes or not world.node_tree:
        return

    nodes = world.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)


def setup_hdr_world(hdr_file, rotation=0.0, blur=0.0):
    assets_dir = get_assets_dir()
    hdr_path = os.path.join(assets_dir, hdr_file)
    if not os.path.isfile(hdr_path):
        print(f"[Skybox] Файл не найден: {hdr_path}")
        return

    # Создаём (или получаем) мир по имени "AddonHDRWorld"
    world_name = "AddonHDRWorld"
    world = bpy.data.worlds.get(world_name)
    if not world:
        world = bpy.data.worlds.new(world_name)

    # Присваиваем миру активной сцене (если ещё не установлен)
    if bpy.context.scene.world != world:
        bpy.context.scene.world = world

    # Включаем ноды
    if not world.use_nodes:
        world.use_nodes = True

    node_tree = world.node_tree
    links = node_tree.links

    # Проверяем, есть ли в node_tree "наш" узел Skybox_Environment
    # Если нет, значит нужно удалить все ноды и создать заново
    node_env = node_tree.nodes.get("Skybox_Environment")
    if not node_env:
        delete_all_world_nodes()

        node_tex_coord = node_tree.nodes.new("ShaderNodeTexCoord")
        node_tex_coord.name = "Skybox_TexCoord"
        node_tex_coord.location = (-800, 0)

        node_mapping = node_tree.nodes.new("ShaderNodeMapping")
        node_mapping.name = "Skybox_Mapping"
        node_mapping.location = (-600, 0)

        node_env = node_tree.nodes.new("ShaderNodeTexEnvironment")
        node_env.name = "Skybox_Environment"
        node_env.label = "HDRI Env"
        node_env.location = (-300, 0)

        node_bg = node_tree.nodes.new("ShaderNodeBackground")
        node_bg.name = "Skybox_Background"
        node_bg.location = (0, 0)

        node_out = node_tree.nodes.new("ShaderNodeOutputWorld")
        node_out.name = "Skybox_Output"
        node_out.location = (200, 0)

        ensure_link(links, node_tex_coord, "Generated", node_mapping, "Vector")
        ensure_link(links, node_mapping, "Vector", node_env, "Vector")
        ensure_link(links, node_env, "Color", node_bg, "Color")
        ensure_link(links, node_bg, "Background", node_out, "Surface")
    else:
        node_mapping = node_tree.nodes.get("Skybox_Mapping")
        node_tex_coord = node_tree.nodes.get("Skybox_TexCoord")
        node_bg = node_tree.nodes.get("Skybox_Background")
        node_out = node_tree.nodes.get("Skybox_Output")

        ensure_link(links, node_tex_coord, "Generated", node_mapping, "Vector")
        ensure_link(links, node_mapping, "Vector", node_env, "Vector")
        ensure_link(links, node_env, "Color", node_bg, "Color")
        ensure_link(links, node_bg, "Background", node_out, "Surface")

    current_image_path = ""
    if node_env.image and node_env.image.filepath:
        current_image_path = bpy.path.abspath(node_env.image.filepath)

    if not current_image_path or os.path.abspath(hdr_path) != os.path.abspath(current_image_path):
        node_env.image = bpy.data.images.load(hdr_path)

    if node_mapping:
        node_mapping.inputs["Rotation"].default_value[2] = math.radians(rotation)


def update_skybox_file(self, context):
    if self.skybox_file:
        setup_hdr_world(self.skybox_file, rotation=self.skybox_rotation)


def update_skybox_rotation(self, context):
    if self.skybox_file:
        setup_hdr_world(self.skybox_file, rotation=self.skybox_rotation)
