import bpy

from .node_utils import (
    get_or_create_node,
    ensure_link
)


def setup_preview_settings(obj, blur=1.0):
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = "//object.png"

    layer_name = "ViewLayer"
    if layer_name not in scene.view_layers:
        print(f"[ERROR] ViewLayer '{layer_name}' не найден!")
        return

    # Активируем нужный ViewLayer
    bpy.context.window.view_layer = scene.view_layers[layer_name]

    # А теперь правим ноды: очищаем все links и подключаем только объект
    if not scene.use_nodes:
        scene.use_nodes = True

    node_tree = scene.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    # Удаляем существующие связи (не трогаем сами узлы)
    for link in list(links):
        links.remove(link)

    # RENDER_LAYERS для объекта:
    node_obj = get_or_create_node(node_tree, 'RENDER_LAYERS', name="Render_Layers_View")
    node_obj.layer = "ViewLayer"

    # Composite + Viewer
    node_view = get_or_create_node(node_tree, 'VIEWER', name="Viewer")
    node_comp = get_or_create_node(node_tree, 'COMPOSITE', name="Composite")

    # Связываем: Object → Composite/Viewer
    ensure_link(links, node_obj, "Image", node_view, "Image")
    ensure_link(links, node_obj, "Image", node_comp, "Image")

    print(f"[INFO] Рендерим объект (ViewLayer) на прозрачном фоне -> {scene.render.filepath}")

    # Блокирующий рендер
    bpy.ops.render.render("EXEC_DEFAULT", write_still=True)
    print("[INFO] Первый рендер (объект) завершён.")

    image_path = bpy.path.abspath(scene.render.filepath)  # Преобразуем "//object.png" в абсолютный путь

    # Создаём/находим Image-ноду
    node_cod_image = get_or_create_node(node_tree, 'IMAGE', name="node_cod_image")

    loaded_img = bpy.data.images.load(image_path)  # Проверка на сохранения проекта
    node_cod_image.image = loaded_img


def setup_preview_settings_last_first_render(compositing_blur):
    scene = bpy.context.scene

    scene.render.film_transparent = False
    scene.render.filepath = "//skybox.png"

    layer_name = "Skybox_Layer"
    if layer_name not in scene.view_layers:
        print(f"[ERROR] ViewLayer '{layer_name}' не найден!")
        return

    # Активируем Skybox-слой
    bpy.context.window.view_layer = scene.view_layers[layer_name]

    # Чтобы при рендере захватить наши новые ноды:
    if not scene.use_nodes:
        scene.use_nodes = True

    node_tree = scene.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    # Удаляем старые связи
    for link in list(links):
        links.remove(link)

    # Создаём/ищем RenderLayers для Skybox и для объекта (если хотите его альфа-оверить поверх)
    node_sky = get_or_create_node(node_tree, 'RENDER_LAYERS', name="Render_Layers_Skybox")
    node_sky.layer = "Skybox_Layer"

    node_cod_image = get_or_create_node(node_tree, 'IMAGE', name="node_cod_image")

    node_obj = get_or_create_node(node_tree, 'RENDER_LAYERS', name="Render_Layers_View")
    node_obj.layer = "ViewLayer"

    node_blur = next((node for node in nodes if node.name == "Blur"), None)

    node_alpha_over_1 = get_or_create_node(
        node_tree, 'CompositorNodeAlphaOver',
        name="Alpha_Over_1",
        location=(-500, 100)
    )
    node_alpha_over_1.inputs["Fac"].default_value = 1.0  # или 0.0 — смотря как хотите

    node_view = get_or_create_node(node_tree, 'VIEWER', name="Viewer")
    node_comp = get_or_create_node(node_tree, 'COMPOSITE', name="Composite")

    ensure_link(links, node_sky, "Image", node_blur, "Image")
    ensure_link(links, node_cod_image, "Image", node_alpha_over_1, node_alpha_over_1.inputs[2].identifier)
    ensure_link(links, node_blur, "Image", node_alpha_over_1, node_alpha_over_1.inputs[1].identifier)
    ensure_link(links, node_alpha_over_1, "Image", node_view, "Image")
    ensure_link(links, node_alpha_over_1, "Image", node_comp, "Image")

    set_blur_size(compositing_blur)

    bpy.ops.render.render("EXEC_DEFAULT", write_still=True)

    bpy.context.window.view_layer = bpy.context.scene.view_layers["ViewLayer"]


def setup_icon_settings(obj):
    """
    Для иконки рендерим один слой (ViewLayer) с прозрачностью
    или без — на ваше усмотрение.
    """
    scene = bpy.context.scene

    # Допустим, иконка тоже на прозрачном.
    scene.render.film_transparent = True

    layer_name = "ViewLayer"
    if layer_name not in scene.view_layers:
        return

    bpy.context.window.view_layer = scene.view_layers[layer_name]

    # Блокирующий рендер
    bpy.ops.render.render("EXEC_DEFAULT", write_still=True)


def setup_compositing_nodes_for_icon():
    """
    Простейший сетап композитинга для иконки:
    один Render Layers -> Composite -> Viewer.
    """
    scene = bpy.context.scene

    if not scene.use_nodes:
        scene.use_nodes = True
        print("[INFO] Compositing: 'Use Nodes' включён.")

    node_tree = scene.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    nodes.clear()

    node_render_view_layer = get_or_create_node(node_tree, 'RENDER_LAYERS', location=(-800, 200))
    node_render_view_layer.layer = "ViewLayer"

    node_view = get_or_create_node(node_tree, 'VIEWER', location=(200, 200))
    node_composite = get_or_create_node(node_tree, 'COMPOSITE', location=(200, 0))

    ensure_link(links, node_render_view_layer, "Image", node_view, "Image")
    ensure_link(links, node_render_view_layer, "Image", node_composite, "Image")

    print("[INFO] Compositing (icon): ноды созданы и связаны.")


def setup_compositing_nodes_for_preview():
    """
    Старый пример, если хотите одним махом собрать
    ViewLayer + Skybox_Layer + Blur + ещё что-то.

    Но мы не используем его напрямую, раз хотим
    два прохода рендера и попеременное переключение.
    """
    scene = bpy.context.scene

    if not scene.use_nodes:
        scene.use_nodes = True
        print("[INFO] Compositing: 'Use Nodes' включён.")

    node_tree = scene.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    nodes.clear()

    node_render_view_layer = get_or_create_node(
        node_tree, 'RENDER_LAYERS',
        name="Render_Layers_View", location=(-800, 200)
    )
    node_render_skybox_layer = get_or_create_node(
        node_tree, 'RENDER_LAYERS',
        name="Render_Layers_Skybox", location=(-800, -100)
    )

    node_render_view_layer.layer = "ViewLayer"
    node_render_skybox_layer.layer = "Skybox_Layer"

    node_blur = get_or_create_node(node_tree, 'BLUR', location=(-500, 100))
    node_blur.use_relative = False
    node_blur.size_x = 100
    node_blur.size_y = 100

    node_alpha_over_1 = get_or_create_node(
        node_tree, 'CompositorNodeAlphaOver',
        name="Alpha_Over_1",
        location=(-500, 100)
    )
    node_alpha_over_1.inputs["Fac"].default_value = 0.0

    node_view = get_or_create_node(node_tree, 'VIEWER', location=(200, 200))
    node_composite = get_or_create_node(node_tree, 'COMPOSITE', location=(200, 0))

    # Примерная связка (не обязательно рабочая «из коробки»):
    # ensure_link(links, node_render_view_layer, "Image", node_alpha_over_1, node_alpha_over_1.inputs[2].identifier)
    ensure_link(links, node_render_skybox_layer, "Image", node_blur, "Image")

    # ensure_link(links, node_blur, "Image", node_alpha_over_1, node_alpha_over_1.inputs[1].identifier)
    # ensure_link(links, node_cod_image, "Image", node_alpha_over_1, node_alpha_over_1.inputs[2].identifier)

    print("[INFO] Compositing (preview): ноды созданы и связаны.")


def set_blur_size(value):
    """
    Устанавливает Size для нода типа 'BLUR' (если он есть).
    """
    scene = bpy.context.scene
    node_tree = scene.node_tree
    node_blur = next((node for node in node_tree.nodes if node.type == 'BLUR'), None)

    if node_blur:
        node_blur.inputs["Size"].default_value = value
        print(f"[INFO] Blur size установлен в {value}")
    else:
        print("[WARNING] BLUR-нод не найден в node_tree!")
