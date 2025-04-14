import os
from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup, Panel
from bpy.props import EnumProperty, FloatProperty, StringProperty
from .skybox_manager import list_skybox_files, setup_hdr_world

class RenderSettings(PropertyGroup):
    render_engine: EnumProperty(
        name="Движок рендера",
        description="Выберите движок рендера",
        items=[
            ('BLENDER_EEVEE_NEXT', "EEVEE Next", ""),
            ('CYCLES', "Cycles", ""),
        ],
        default='BLENDER_EEVEE_NEXT'
    )

    # --- Параметры для вкладки "Камера" ---

    camera_position: EnumProperty(
        name="Позиция камеры",
        description="Положение камеры относительно объекта",
        items=[
            ('GENERAL', "Общий план", "Камера общего плана"),
            ('LEFT', "Слева", "Камера слева"),
            ('RIGHT', "Справа", "Камера справа"),
        ],
        default='GENERAL'
    )

    camera_distance: FloatProperty(
        name="Camera Distance",
        description="Дистанция Камеры",
        default=2.5,
        min=-0.0,
        max=5.0,
    )

    # --- Параметры для вкладки "Композитор" ---

    compositing_blur: FloatProperty(
        name="Blur",
        description="Размытие заднего фона",
        default=0.0,
        min=-0.0,
        max=1.0,
    )

    # --- Параметры для вкладки "Скайбокс" ---

    def update_skybox_file(self, context):
        if self.skybox_file:
            setup_hdr_world(self.skybox_file, rotation=self.skybox_rotation)

    def update_skybox_rotation(self, context):
        if self.skybox_file:
            setup_hdr_world(self.skybox_file, rotation=self.skybox_rotation)

    skybox_file: EnumProperty(
        name="Skybox",
        description="Выберите HDRI из папки assets",
        items=lambda self, context: list_skybox_files(),
        update=update_skybox_file
    )

    skybox_rotation: FloatProperty(
        name="Rotation",
        description="Поворот HDRI по Z",
        default=0.0,
        min=-360.0,
        max=360.0,
        update=update_skybox_rotation
    )

    save_path: StringProperty(
        name="Save Path",
        description="Путь для сохранения рендеров",
        subtype='DIR_PATH',
        default=os.path.join(os.path.expanduser("~"), "Desktop")  # Рабочий стол
    )


class OBJECT_PT_MainPanel(Panel):
    bl_label = "Kartoteka Preview"
    bl_idname = "OBJECT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kartoteka'
    # bl_order = 0  # Порядок отображения (самая верхняя панель в категории)
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Быстрое превью объекта")

        layout.separator()

        # Кнопка "Создать превью"
        layout.operator("object.render_object_preview",
                        text="Создать превью 1:1",
                        icon='RENDER_STILL')

        # Кнопка "Создать иконку" (использует другой оператор!)
        layout.operator("object.render_object_icon",
                        text="Создать иконку формы 3:4",
                        icon='RESTRICT_RENDER_OFF')

        layout.prop(context.scene.render_settings, "save_path", text="Путь сохранения")
        layout.operator("object.set_save_path", text="Выбрать путь")


class OBJECT_PT_RenderPanel(Panel):
    bl_label = "Настройки рендера"
    bl_idname = "OBJECT_PT_render_panel"
    bl_parent_id = "OBJECT_PT_main_panel"  # Указываем родительскую панель
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KARTOTEKA.Addons'
    bl_order = 1  # Порядок отображения среди подпанелей

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Свойства из PropertyGroup
        layout.prop(scene.render_settings, "render_engine", text="Движок")
        layout.prop(scene.render_settings, "camera_position", text="Камера")
        layout.prop(scene.render_settings, "camera_distance", text="Дистанция")

        layout.separator()


class OBJECT_PT_SkyboxPanel(Panel):
    bl_label = "Настройки Skybox"
    bl_idname = "OBJECT_PT_skybox_panel"
    bl_parent_id = "OBJECT_PT_main_panel"  # Указываем родительскую панель
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KARTOTEKA.Addons'
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene.render_settings, "skybox_file", text="HDRI")
        layout.prop(scene.render_settings, "skybox_rotation", text="Rotation")


class OBJECT_PT_CompositingPanel(Panel):
    bl_label = "Настройки Compositing"
    bl_idname = "OBJECT_PT_compositing_panel"
    bl_parent_id = "OBJECT_PT_main_panel"  # Указываем родительскую панель
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KARTOTEKA.Addons'
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene.render_settings, "compositing_blur", text="Blur")

def register():
    register_class(RenderSettings)
    register_class(OBJECT_PT_MainPanel)
    register_class(OBJECT_PT_RenderPanel)
    register_class(OBJECT_PT_SkyboxPanel)
    register_class(OBJECT_PT_CompositingPanel)


def unregister():
    unregister_class(OBJECT_PT_CompositingPanel)
    unregister_class(OBJECT_PT_SkyboxPanel)
    unregister_class(OBJECT_PT_RenderPanel)
    unregister_class(OBJECT_PT_MainPanel)
    unregister_class(RenderSettings)