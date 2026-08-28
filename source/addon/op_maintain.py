import bpy
from pathlib import Path
from glob import glob
from . utils_operators import return_init
from . utils_maintain import clean_backup_folder
from . utils_file import get_all_save_versions
from . utils_maintain import fix_backup_continuity, get_orphans


class VK_OT_CBF_CleanUpOneFile(bpy.types.Operator):
    bl_idname = "vk_cbf.cleanup_one_file"
    bl_label = 'CleanUpBackupfolder'
    bl_description = "Clean a backup folder keeping only the necessary number of Save Versions" \
                     "\nOnly project related files are affected"

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "This operation requires a project file to be opened")
            return {'CANCELLED'}
        base_name, _, backup_dir = inits
        if not clean_backup_folder(base_name, backup_dir):
            self.report({"ERROR"}, "Error cleaning up a backup folder")
            return {'CANCELLED'}
        return {"FINISHED"}


class VK_OT_CBF_CleanUpAllFiles(bpy.types.Operator):
    bl_idname = "vk_cbf.cleanup_all_files"
    bl_label = 'CleanUpBackupfolder'
    bl_description = "Clean up the backup folder keeping only necessary number of Save Versions" \
                     "\nAll files are affected"

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "This operation requires a project file to be opened")
            return {'CANCELLED'}
        _, _, backup_dir = inits

        files = get_all_save_versions(backup_dir)
        if not files:
            self.report({"WARNING"}, "Nothing to process")
            return {'CANCELLED'}
        for base_name in files:
            if not clean_backup_folder(base_name, backup_dir):
                self.report({"ERROR"}, "Error cleaning up a backup folder")
                return {'CANCELLED'}
        return {"FINISHED"}


class VK_OT_FixIntegrity(bpy.types.Operator):
    bl_idname = "vk_cbf.fix_integrity"
    bl_label = "Fix"
    bl_description = "Fix discontinued Save Versions"

    @staticmethod
    def __save_version2int(save_version):
        return int(save_version[len(Path(save_version).with_suffix(".blend").name):])

    @staticmethod
    def check_continuity(save_versions):
        number_ver = sorted(VK_OT_FixIntegrity.__save_version2int(e) for e in save_versions)
        return ((number_ver[-1] - number_ver[0] + 1) == len(number_ver)) and (number_ver[0] == 1)

    @staticmethod
    def should_execute(inits) -> tuple[set[str], str, set[str]]:
        if not inits:
            return {'WARNING'}, "Please open a Blender file", {'CANCELLED'}
        base_name, _, _ = inits
        if Path(base_name).suffix != ".blend":
            return {'WARNING'}, "The current file is a Save Version", {'CANCELLED'}
        return {'INFO'}, "", {'FINISHED'}

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def invoke(self, context, event):
        inits = return_init()
        report_type, msg, action = self.should_execute(inits)
        if 'CANCELLED' in action:
            self.report(report_type, msg)
            return {'CANCELLED'}
        base_name, _, backup_dir = inits
        save_versions = glob(pathname=f"{Path(base_name).stem}.blend[0-9]*", root_dir=backup_dir)
        if not save_versions:
            self.report({'WARNING'}, "Save Versions not found")
            return {'CANCELLED'}
        if self.check_continuity(save_versions):
            self.report({'INFO'}, "Valid backup integrity")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        inits = return_init()
        base_name, _, backup_dir = inits
        report_type, msg, action = fix_backup_continuity(base_name, backup_dir)
        if 'CANCELLED' in action:
            self.report(report_type, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, "Backup continuity fixed")
        return {'FINISHED'}


class VK_OT_CBF_ListOrphans(bpy.types.Operator):
    bl_label = "List of orphans"
    bl_idname = "vk_cbf.list_orphans"
    bl_description = "Shows a list of Save Version not associated with any existing project files"

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        inits = return_init()
        if not inits:
            self.report({"ERROR"}, "This operation requires a project file to be opened")
            return {'CANCELLED'}
        return context.window_manager.invoke_popup(self, width=320)

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.label(text=self.bl_label, icon='INFO')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="List of orphaned Save Versions not linked to any Blender file:")
        col.separator(factor=1.0)

        _, src_dir, backup_dir = return_init()
        orphans = get_orphans(src_dir, backup_dir)
        if not orphans:
            row = col.row(align=True)
            row.label(text="      No orphans found")
            return None

        orphans = sorted(orphans.items(), key=lambda e: e[0])
        suffix_grp = "*"
        suffix_sgl = "?"
        for k, v in orphans:
            output = "    " + k
            output += suffix_sgl if v == 1 else suffix_grp
            row = col.row(align=True)
            row.label(text=output)

        layout.separator()
        col = layout.column(align=True)
        col.label(text=f"{suffix_sgl} - this suffix depicts a single file")
        col.label(text=f"{suffix_grp} - this suffix depicts a group of files")
