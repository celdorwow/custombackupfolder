from bpy.props import StringProperty
import bpy
from . utils_operators import return_init
from . utils_maintain import calculate_backups
from . utils_misc import get_formated_size


def report(is_valid_backup: bool) -> None:
    if is_valid_backup:
        message = "Save Version successfully created"
        type = "INFO"
    else:
        message = "Error creating Save Version from the current file"
        type = "ERROR"
    VK_OT_CBF_IssueReport.bl_message = message
    VK_OT_CBF_IssueReport.bl_mtype = type
    bpy.ops.vk_cbf.report(
        message=message,
        mtype=type,
    )


class VK_OT_CBF_IssueReport(bpy.types.Operator):
    bl_idname = 'vk_cbf.report'
    bl_label = 'ReportStatus'
    bl_description = "Issue report"

    message: StringProperty(default="Default")
    mtype: StringProperty(default="INFO")

    def execute(self, context):
        self.report({self.mtype}, self.message)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Custom Interface!")


class VK_OT_CBF_SumUpBackups(bpy.types.Operator):
    bl_idname = 'vk_cbf.sumup'
    bl_label = 'SumUpBackups'
    bl_description = "Summary of the backup folder" \
                     "\nReport of the total size of all existing Save Versions." \
                     "\nDisplays two sums: a sum of project related files, all files."

    @classmethod
    def poll(cls, context):
        inits = return_init()
        return inits is not None

    def execute(self, context):
        backups = calculate_backups()
        if not backups:
            self.report({"ERROR"}, "Please, open a project file")
            return {'CANCELLED'}

        sum_current, sum_all = backups
        output = f"\nCurrent file: {get_formated_size(sum_current)}." \
                 f" All files: {get_formated_size(sum_all)}"
        self.report({"INFO"}, output)
        return {'FINISHED'}
