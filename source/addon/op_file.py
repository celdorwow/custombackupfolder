import bpy
import bpy_extras
import os
from bpy.props import StringProperty
from pathlib import Path
from glob import glob
from . utils_operators import return_init
from . utils_file import (
    get_all_save_versions,
    rename_copies,
    move_copies,
    is_main_file,
)


class VK_OT_CBF_RenameFiles(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Operator: provides a button to rename Save Versions to associate orphan Save Versions back with a project file"""
    bl_idname = "vk_cbf.rename_files"
    bl_label = "Select File"
    bl_description = ("Select one file from a sequence of Save Versions or Cancel\n"
                      "This process will rename the whole sequence of files and associate the files\n"
                      "back with the project file.\n")

    filter_glob: StringProperty(
        default='*.blend[0-9]*;*.blend',
        options={'HIDDEN'}
    )

    filepath = bpy.props.StringProperty(
        name="File Path",
    )

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "This operation requires an opened file")
            return {'CANCELLED'}

        base_name, _, backup_dir = inits
        msg_type, msg, output = rename_copies(base_name, Path(self.filepath).name, backup_dir)
        if "ERROR" in msg_type:
            self.report(msg_type, msg)
            return {'CANCELLED'}
        self.report({"INFO"}, "Successfully renamed Save Versions")
        return {'FINISHED'}

    def invoke(self, context, event):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "Please, open a project file")
            return {'CANCELLED'}
        _, _, backup_dir = inits
        self.filepath = backup_dir + os.sep
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class VK_OT_CBF_MoveFiles(bpy.types.Operator):
    """Move files"""
    bl_idname = "vk_cbf.move_files"
    bl_label = "Move files"
    bl_description = "Move project related Saved Versions to a custom backup folder" \
                     "\nFiles are sorted by a modification date"

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "This operation requires an opened file")
            return {'CANCELLED'}
        base_name, src_dir, backup_dir = inits
        os.makedirs(backup_dir, exist_ok=True)
        move_copies(base_name, src_dir, backup_dir)
        return {'FINISHED'}


class VK_OT_CBF_MoveAllFiles(bpy.types.Operator):
    """Move all existing saves"""
    bl_idname = "vk_cbf.move_all_files"
    bl_label = "Move All Files"
    bl_description = "Move all Saved Versions to a custom backup folder." \
            "\nAll files are sorted in the reverse order by a modification date"

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "This operation requires an opened file")
            return {'CANCELLED'}
        _, src_dir, backup_dir = inits
        os.makedirs(backup_dir, exist_ok=True)

        # Move all existing save files
        files = get_all_save_versions(src_dir, backup_dir)
        for base_name in files:
            move_copies(base_name, src_dir, backup_dir)
        return {'FINISHED'}


class VK_EU_CBF_OpenCurrentFile(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "vk_cbf.open_browser_current"
    bl_label = "Browse Current"
    bl_description = "Open file window to browse Save Versions in a backup folder"

    filter_glob: StringProperty(
        options={'HIDDEN'}
    )

    filepath = bpy.props.StringProperty(
        name="File Path",
    )

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        print("--->", self.filter_glob)
        bpy.ops.wm.open_mainfile(filepath=self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "Please, open a project file")
            return {'CANCELLED'}
        base_name, _, backup_dir = inits
        self.filter_glob = f"*{Path(base_name).stem}.blend[0-9]*"
        self.filepath = backup_dir + os.sep
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class VK_EU_CBF_OpenAllFiles(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "vk_cbf.open_filebrowser_all"
    bl_label = "Open File"
    bl_description = "Browse backup folder for the other Save Versions"

    filter_glob: StringProperty(
        default='*.blend[0-9]*;*.blend',
        options={'HIDDEN'}
    )

    filepath = bpy.props.StringProperty(
        name="File Path",
    )

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        bpy.ops.wm.open_mainfile(filepath=self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "Please, open a project file")
            return {'CANCELLED'}
        _, _, backup_dir = inits
        self.filepath = backup_dir + os.sep
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class VK_OT_CBF_OpenPrevious(bpy.types.Operator):
    bl_idname = "vk_cbf.open_previous"
    bl_label = "Previous"
    bl_description = "Open previous Save Version"

    @staticmethod
    def set_previous() -> tuple[set[str], str, set[str]]:
        scene = bpy.types.Scene
        scene.vk_cbf_prev_exists = False
        scene.vk_cbf_path_name = ""
        inits = return_init()
        if not inits:
            return {'WARNING'}, "Please open a Blender file", {'CANCELLED'}
        base_name, src_dir, backup_dir = inits
        path_dir = src_dir
        if is_main_file(inits):
            path_dir = backup_dir
        save_versions = glob(pathname=f"{Path(base_name).stem}.blend[0-9]*", root_dir=path_dir)
        if not save_versions:
            return {'WARNING'}, "No more further Save Version found", {'CANCELLED'}
        save_versions = sorted(save_versions)
        if is_main_file(inits):
            save_versions.insert(0, base_name)
        i_save_ver = save_versions.index(base_name)
        if i_save_ver + 1 >= len(save_versions):
            return {'WARNING'}, "No more Save Versions", {'CANCELLED'}
        p_prev = Path(path_dir, save_versions[i_save_ver + 1])
        scene.vk_cbf_path_name = str(p_prev)
        scene.vk_cbf_prev_exists = p_prev.exists()
        return {'FINISHED'}, "", {'INFO'}

    @classmethod
    def poll(cls, context):
        return context.scene.vk_cbf_prev_exists

    def invoke(self, context, event):
        report_type, msg, action = self.set_previous()
        if "CANCELLED" in action:
            self.report(report_type, msg)
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if not scene.vk_cbf_prev_exists:
            self.report({'WARNING'}, "The previous Save Version does not exist")
            return {'CANCELLED'}
        bpy.ops.wm.open_mainfile(filepath=scene.vk_cbf_path_name)
        return {'FINISHED'}


class VK_OT_CBF_OpenNext(bpy.types.Operator):
    bl_idname = "vk_cbf.open_next"
    bl_label = "Next"
    bl_description = "Open next Save Version up to the current file"

    @staticmethod
    def set_next():
        scene = bpy.types.Scene
        scene.vk_cbf_next_exists = False
        scene.vk_cbf_path_name = ""
        inits = return_init()
        if not inits:
            return {'WARNING'}, "Please open a Blender file", {'CANCELLED'}
        if is_main_file(inits):
            return {'WARNING'}, "This is the main file", {'CANCELLED'}
        base_name, src_dir, _ = inits
        save_versions = glob(pathname=f"{Path(base_name).stem}.blend[0-9]*", root_dir=src_dir)
        if not save_versions:
            return {'WARNING'}, "None of Save Versions found", {'CANCELLED'}
        save_versions = sorted(save_versions)
        i_save_ver = save_versions.index(base_name)
        if i_save_ver == 0:
            p_next = Path(*Path(src_dir).parts[:-1]) / Path(base_name).with_suffix(".blend")
        else:
            p_next = Path(src_dir, save_versions[i_save_ver - 1])
        scene.vk_cbf_path_name = str(p_next)
        scene.vk_cbf_next_exists = p_next.exists()
        return {'FINISHED'}, "", {'INFO'}

    @classmethod
    def poll(cls, context):
        return context.scene.vk_cbf_next_exists

    def invoke(self, context, event):
        report_type, msg, action = self.set_next()
        if "CANCELLED" in action:
            self.report(report_type, msg)
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if not scene.vk_cbf_next_exists:
            self.report({'WARNING'}, "The next Save Version does not exist")
            return {'CANCELLED'}
        bpy.ops.wm.open_mainfile(filepath=scene.vk_cbf_path_name)
        return {'FINISHED'}
