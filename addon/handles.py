import bpy
import os
from bpy.app.handlers import persistent
from . op_file import VK_OT_CBF_OpenPrevious, VK_OT_CBF_OpenNext
from . op_report import report
from . ui_functions import prefs_object
from . utils_maintain import clean_backup_folder
from . utils_file import FileValidator, make_copies
from . utils_operators import return_init


@persistent
def post_load_checks(_):
    VK_OT_CBF_OpenPrevious.set_previous()
    VK_OT_CBF_OpenNext.set_next()


@persistent
def calculate_checksum(_) -> None:
    blend_path = bpy.data.filepath
    if not blend_path:
        return None

    prefs = prefs_object()
    if prefs.is_on_pause:
        return None

    wm = bpy.types.WindowManager
    checksums = bpy.context.scene.checksums

    # Save current file validator
    wm.fileValidator = FileValidator(blend_path, checksums.check_sum)


@persistent
def move_blend_save_versions(_) -> None:
    inits = return_init()
    if not inits:
        return None

    prefs = prefs_object()
    if prefs.is_on_pause:
        return None

    wm = bpy.types.WindowManager
    base_name, src_dir, backup_dir = inits
    os.makedirs(backup_dir, exist_ok=True)
    prefs.base_name = base_name

    # Make copies in the backup folder
    make_copies(base_name, src_dir, backup_dir)

    # Clean folder from exceeding files
    if prefs.auto_cleanup:
        clean_backup_folder(base_name, backup_dir)

    # Check a new save version is the same
    new_save_ver = os.path.join(backup_dir, f"{base_name}1")
    report(wm.fileValidator.compare(new_save_ver))

    # Check/Set flags for Previous and Next buttons
    VK_OT_CBF_OpenPrevious.set_previous()
    VK_OT_CBF_OpenNext.set_next()
