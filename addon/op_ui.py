import bpy
from bpy.props import IntProperty, BoolProperty, StringProperty, EnumProperty
from . utils_operators import update_on_pause
from .. import __package__ as base_package
from .. import ADDON_NAME


class VK_ChecksumProperties(bpy.types.PropertyGroup):
    # Reference
    check_sum: EnumProperty(
        name="Verification method",
        description="Select a backup verification method\n" \
                    "Any hash-related algorithm will take longer on save",
        items=[
            ("FILESIZE", "File Size", ""),
            ("MD5", "Hash File MD5", ""),
            ("SHA1", "Hash File SHA1", ""),
        ],
    )


class VK_EU_CBF_OpenPreferences(bpy.types.Operator):
    bl_idname = "vk_cbf.open_addon_preferences"
    bl_label = "Open Addon Preferences"

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        bpy.context.preferences.active_section = 'ADDONS'
        bpy.context.window_manager.addon_search = ADDON_NAME
        return {'FINISHED'}


class VK_PT_CBF_SidePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_SidePanel"
    bl_label = "Custom Backup Folder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CBF"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        factor = 0.7

        layout.operator("vk_cbf.open_addon_preferences", text="Open Preferences", icon="PREFERENCES")
        layout.separator()

        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.label(text="", icon="TRIA_LEFT")
        row.operator("vk_cbf.open_previous", text="Previous")
        row.operator("vk_cbf.open_next", text="Next")
        row.label(text="", icon="TRIA_RIGHT")
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Search for Save Versions")
        c = split.column()
        c.operator('vk_cbf.open_filebrowser_all', text="Browse")

        layout.separator()

        box = layout.box()
        box.label(text="Move Saved Versions", icon='DOCUMENTS')

        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Current project file")
        c = split.column()
        c.operator("vk_cbf.move_files", text="Move")
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="All project files")
        c = split.column()
        c.operator("vk_cbf.move_all_files", text="Move All")

        layout.separator()

        box = layout.box()
        box.label(text="Clean up a backup folder", icon='BRUSHES_ALL')
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Current project file")
        c = split.column()
        c.operator("vk_cbf.cleanup_one_file", text="Clean")
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="All project files")
        c = split.column()
        c.operator("vk_cbf.cleanup_all_files", text="Clean All")

        layout.separator()

        box = layout.box()
        box.label(text="Rename Save Versions", icon='DOCUMENTS')
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Select any Save Version")
        c = split.column()
        c.operator("vk_cbf.rename_files", text="Rename")

        layout.separator()

        box = layout.box()
        box.label(text="Fix backup integrity", icon='DOCUMENTS')
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Press button to fix backups")
        c = split.column()
        c.operator("vk_cbf.fix_integrity", text="Fix")

        layout.separator()

        box = layout.box()
        box.label(text="Reports", icon='INFO')
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Report backup folder size")
        c = split.column()
        c.operator("vk_cbf.sumup", text="Report")
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Show list of orphans")
        c = split.column()
        c.operator("vk_cbf.list_orphans", text="Show")


class VK_PT_CBF_Popover(bpy.types.Panel):
    """Panel for a popover"""
    bl_label = "CBF"
    bl_idname = "VK_PT_CBF_button_popover"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        factor = 0.7

        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.label(text="", icon="TRIA_LEFT")
        row.operator("vk_cbf.open_previous", text="Previous")
        row.operator("vk_cbf.open_next", text="Next")
        row.label(text="", icon="TRIA_RIGHT")
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Search for backups")
        c = split.column()
        c.operator('vk_cbf.open_filebrowser_all', text="Browse")

        box = layout.box()
        box.label(text="Reports", icon='INFO')
        box.row()
        c = box.column()
        row = c.row()
        split = row.split(factor=factor)
        c = split.column()
        c.label(text="Report backup size")
        c = split.column()
        c.operator("vk_cbf.sumup", text="Report")


class VK_PT_CBF_SaveVersionPreferences(bpy.types.AddonPreferences):
    bl_idname = base_package

    save_versions: IntProperty(
        name="Save Versions",
        description="A number of temporary backup files." \
                    "\nTakes over the built-in \"Save Versions\" in Preferences for the purpose of this addon.",
        default=25,
        min=0,
        max=999,
    )

    backup_folder_name: StringProperty(
        name="Backup Folder Name",
        default=".tempsaves",
    )

    auto_cleanup: BoolProperty(
        name="Auto Clean",
        description="Automatically clean up a backup folder on save.\nOnly the current file is affected",
        default=False,
    )

    can_rename_overwrite: BoolProperty(
        name="Overwrite Renamed Files",
        description="If this option is enabled, the renaming process can overwrite existing files.",
        default=False,
    )

    is_on_pause: BoolProperty(
        name="Pause",
        description="When enabled, addon will not process Save Versions",
        update=update_on_pause,
        default=False,
    )

    old_save_versions: IntProperty(
        name="Save Versions Bckup",
        min=0,
        max=999,
    )

    is_save_versions_changed: BoolProperty(
        name="Is Save Versions Changed",
        default=False,
        options={'HIDDEN'},
    )

    base_name: StringProperty(
        name="Base Name",
        description="A name of the main file",
        options={'HIDDEN'}
    )

    file_hash: StringProperty(
        default="",
        options={'HIDDEN'},
    )

    file_size: IntProperty(
        default=0,
        options={'HIDDEN'},
    )

    def draw(self, context):
        layout = self.layout
        checksums = context.scene.checksums

        layout.prop(self, "save_versions")
        layout.separator()
        layout.prop(self, "backup_folder_name")

        layout.separator()
        layout.prop(checksums, "check_sum")

        layout.separator()
        row = layout.row()
        row.prop(self, "auto_cleanup")
        row.prop(self, "is_on_pause")
