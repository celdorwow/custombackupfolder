import bpy
from bpy.props import PointerProperty, BoolProperty, StringProperty
from . import handles
from . import op_file, op_maintain, op_report, op_ui
from . import ui_functions


classes = (
    op_report.VK_OT_CBF_IssueReport,
    op_report.VK_OT_CBF_SumUpBackups,
    op_file.VK_OT_CBF_RenameFiles,
    op_file.VK_OT_CBF_MoveFiles,
    op_file.VK_OT_CBF_MoveAllFiles,
    op_file.VK_EU_CBF_OpenCurrentFile,
    op_file.VK_EU_CBF_OpenAllFiles,
    op_file.VK_OT_CBF_OpenPrevious,
    op_file.VK_OT_CBF_OpenNext,
    op_maintain.VK_OT_CBF_CleanUpOneFile,
    op_maintain.VK_OT_CBF_CleanUpAllFiles,
    op_maintain.VK_OT_FixIntegrity,
    op_maintain.VK_OT_CBF_ListOrphans,
    op_ui.VK_ChecksumProperties,
    op_ui.VK_EU_CBF_OpenPreferences,
    op_ui.VK_PT_CBF_SaveVersionPreferences,
    op_ui.VK_PT_CBF_SidePanel,
    op_ui.VK_PT_CBF_Popover,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if handles.post_load_checks not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(handles.post_load_checks)
    if handles.calculate_checksum not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(handles.calculate_checksum)
    if handles.move_blend_save_versions not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(handles.move_blend_save_versions)
    ui_functions.process_buildin_save_versions(init=True)
    bpy.types.VIEW3D_MT_editor_menus.append(ui_functions.vk_cbf_define_prev_next_popover)
    bpy.types.Scene.checksums = PointerProperty(type=op_ui.VK_ChecksumProperties)
    bpy.types.Scene.vk_cbf_prev_exists = BoolProperty(default=False)
    bpy.types.Scene.vk_cbf_next_exists = BoolProperty(default=False)
    bpy.types.Scene.vk_cbf_path_name = StringProperty(subtype="FILE_PATH")


def unregister():
    del bpy.types.Scene.vk_cbf_path_name
    del bpy.types.Scene.vk_cbf_next_exists
    del bpy.types.Scene.vk_cbf_prev_exists
    del bpy.types.Scene.checksums
    bpy.types.VIEW3D_MT_editor_menus.remove(ui_functions.vk_cbf_define_prev_next_popover)
    ui_functions.process_buildin_save_versions(init=False)
    if handles.move_blend_save_versions in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(handles.move_blend_save_versions)
    if handles.calculate_checksum in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(handles.calculate_checksum)
    if handles.post_load_checks in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(handles.post_load_checks)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
