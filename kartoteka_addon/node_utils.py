def find_node_by_label(node_tree, label):
    """Найдёт первый узел, у которого node.label == label."""
    for node in node_tree.nodes:
        if node.label == label:
            return node
    return None


def find_node_by_type(node_tree, node_type):
    for node in node_tree.nodes:
        if node.type == node_type:
            return node
    return None


def get_or_create_node(node_tree, node_type, label=None, name=None, location=(0, 0)):
    """
    Ищет узел по типу, имени и label.
    Если такой узел уже есть, возвращает его. Если нет — создаёт новый.
    """
    bl_node_type = _bl_node_type_from_enum(node_type)

    print(f"[DEBUG] Ищем узел типа {node_type} ({bl_node_type})...")

    for node in node_tree.nodes:
        if node.bl_idname == bl_node_type:
            if name and node.name.startswith(name):
                print(f"[DEBUG] Найден существующий узел (по имени): {node.name}")
                return node  # Узел с таким именем найден, возвращаем его
            if label and node.label == label:
                print(f"[DEBUG] Найден существующий узел (по label): {node.label}")
                return node  # Узел с таким label найден, возвращаем его

    # Если name передан, проверим, не существует ли узел с таким же именем (с учетом Blender-суффиксов .001 и т. д.)
    existing_names = {node.name for node in node_tree.nodes}
    if name in existing_names:
        base_name = name
        counter = 1
        while f"{base_name}.{counter:03d}" in existing_names:
            counter += 1
        name = f"{base_name}.{counter:03d}"
        print(f"[WARNING] Имя '{base_name}' уже занято, новый узел будет назван '{name}'.")

    # Создаём новый узел
    print(f"[DEBUG] Создаём новый узел {bl_node_type} с именем {name}...")
    node = node_tree.nodes.new(bl_node_type)
    node.location = location
    if label:
        node.label = label
    if name:
        node.name = name  # Назначаем имя, учитывая возможное изменение

    print(f"[DEBUG] Создан новый узел: {node_type} ({node.name})")
    return node



def _bl_node_type_from_enum(node_type):
    """
    Простая функция, чтобы вернуть фактическое имя класса,
    если вы используете короткую форму 'TEX_ENVIRONMENT' и т.п.
    """
    mapping = {
        'TEX_COORD': "ShaderNodeTexCoord",
        'MAPPING': "ShaderNodeMapping",
        'TEX_ENVIRONMENT': "ShaderNodeTexEnvironment",
        'BACKGROUND': "ShaderNodeBackground",
        'OUTPUT_WORLD': "ShaderNodeOutputWorld",
        'RENDER_LAYERS': "CompositorNodeRLayers",
        'BLUR': "CompositorNodeBlur",
        'ALPHA_OVER': "CompositorNodeAlphaOver",
        'VIEWER': "CompositorNodeViewer",
        'COMPOSITE': "CompositorNodeComposite",
        'IMAGE': "CompositorNodeImage",
    }
    return mapping.get(node_type, node_type)


def ensure_link(links, from_node, from_socket_name, to_node, to_socket_name):
    """
    Проверяет, есть ли уже линк от from_node.outputs[from_socket_name]
    к to_node.inputs[to_socket_name]. Если нет — создаёт.
    """
    out_socket = from_node.outputs.get(from_socket_name)
    in_socket = to_node.inputs.get(to_socket_name)

    if not out_socket or not in_socket:
        return

    # Проверим, нет ли уже такого линка
    for link in links:
        if link.from_socket == out_socket and link.to_socket == in_socket:
            return  # уже связаны

    links.new(out_socket, in_socket)
