import bpy


def get_or_create_object_collection(obj, base_name="Wall_Collection"):
    """
    Определяет коллекцию объекта. Если он не состоит ни в одной коллекции, создаёт новую.
    Позволяет задать имя коллекции для удобного доступа.
    """
    if not obj.users_collection:
        # Объект не в коллекции → создаём новую
        collection = bpy.data.collections.get(base_name)
        if not collection:
            collection = bpy.data.collections.new(base_name)
            bpy.context.scene.collection.children.link(collection)
            print(f"[INFO] Создана новая коллекция: {base_name}")

        collection.objects.link(obj)
        print(f"[INFO] Объект '{obj.name}' добавлен в коллекцию '{base_name}'")
        return collection

    # Если объект уже в коллекции, возвращаем первую его коллекцию
    return obj.users_collection[0]


def ensure_object_in_collection(obj):
    """
    Проверяет, состоит ли объект в коллекции. Если нет — перемещает его в нужную.
    """
    collection = get_or_create_object_collection(obj)
    print(f"[INFO] Объект '{obj.name}' уже в коллекции '{collection.name}'")


def setup_skybox_view_layer():
    """
    Создаёт ViewLayer 'Skybox_Layer' и отключает все коллекции, кроме Scene Collection.
    """
    view_layer_name = "Skybox_Layer"

    # Создаём новый ViewLayer, если его нет
    if view_layer_name not in bpy.context.scene.view_layers:
        bpy.context.scene.view_layers.new(name=view_layer_name)
        print(f"[INFO] Создан новый ViewLayer: {view_layer_name}")

    view_layer = bpy.context.scene.view_layers[view_layer_name]

    # Отключаем все коллекции, кроме Scene Collection
    for collection in bpy.data.collections:
        layer_collection = view_layer.layer_collection.children.get(collection.name)
        if layer_collection:
            layer_collection.exclude = True

    print(f"[INFO] Настроен ViewLayer: {view_layer_name}. Все коллекции, кроме Scene Collection, отключены.")


def activate_view_layer():

    view_layer_name = "ViewLayer"

    if view_layer_name in bpy.context.scene.view_layers:
        bpy.context.window.view_layer = bpy.context.scene.view_layers[view_layer_name]
        print(f"[INFO] ViewLayer '{view_layer_name}' активирован.")
    else:
        print(f"[WARNING] ViewLayer '{view_layer_name}' не найден. Возможно, его нужно сначала создать.")


def activate_skybox_view_layer():
    """
    Делает 'Skybox_Layer' активным.
    """
    view_layer_name = "Skybox_Layer"

    if view_layer_name in bpy.context.scene.view_layers:
        bpy.context.window.view_layer = bpy.context.scene.view_layers[view_layer_name]
        print(f"[INFO] ViewLayer '{view_layer_name}' активирован.")
    else:
        print(f"[WARNING] ViewLayer '{view_layer_name}' не найден. Возможно, его нужно сначала создать.")


def set_film_transparency(enable: bool):
    """
    Включает или выключает прозрачность фона в рендере.
    :param enable: True - включает Transparent, False - выключает.
    """
    scene = bpy.context.scene
    scene.render.film_transparent = enable
    state = "включена" if enable else "выключена"
    print(f"[INFO] Прозрачность фона рендера {state}.")
