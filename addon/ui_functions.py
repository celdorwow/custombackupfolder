import bpy
from .. import __package__ as base_package


def prefs_object():
    return bpy.context.preferences.addons[base_package].preferences


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


def vk_cbf_define_prev_next_popover(self, context):
    """Button in the header"""
    layout = self.layout
    layout.popover(
        panel="VK_PT_CBF_button_popover",  # should display the above Panel
        text="CBF",
        icon='DOCUMENTS'
    )
