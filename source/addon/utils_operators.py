import bpy
import os
from . ui_functions import prefs_object


def return_init() -> tuple[str, str, str] | None:
    blend_path = bpy.data.filepath
    if not blend_path:
        return None
    prefs = prefs_object()
    src_dir = str(os.path.dirname(blend_path))
    backup_dir = str(os.path.join(src_dir, prefs.backup_folder_name))
    base_name = str(os.path.basename(blend_path))
    return base_name, src_dir, backup_dir


def process_buildin_save_versions(init: bool) -> None:
    """Process built-in Save Versions for the purpose of the addon
    init: bool
        True means addon take over the property. Otherwise, the property is recovered from its original value"""
    prefs = prefs_object()
    filepaths = bpy.context.preferences.filepaths
    if init:
        if filepaths.save_version == 0:
            prefs.old_save_versions = filepaths.save_version
            prefs.is_save_versions_changed = True
            filepaths.save_version = 1
    else:
        if prefs.is_save_versions_changed:
            filepaths.save_version = prefs.old_save_versions


def update_on_pause(self, context):
    """This is a handler to update Blender System Settings when CBF change between
    states: on pause and active"""
    prefs = prefs_object()
    process_buildin_save_versions(not prefs.is_on_pause)
