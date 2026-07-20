import bpy
import shutil
import typing
import hashlib
import os
import bpy_extras
from enum import Enum
from bpy.app.handlers import persistent
from bpy.props import IntProperty, StringProperty, BoolProperty, EnumProperty
from glob import glob, iglob
from pathlib import Path


def version2str(value: str|tuple[int, int, int]):
    if isinstance(value, str):
        return value
    return ".".join(map(lambda x: str(x), value))


def prefs_object():
    return bpy.context.preferences.addons[__name__].preferences


def return_init() -> tuple[str, str, str] | None:
    blend_path = bpy.data.filepath
    if not blend_path:
        return None
    prefs = prefs_object()
    src_dir = os.path.dirname(blend_path)
    backup_dir = os.path.join(src_dir, prefs.backup_folder_name)
    base_name = os.path.basename(blend_path)
    return base_name, src_dir, backup_dir


def get_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f_h:
        data = f_h.read()
        return hashlib.md5(data).hexdigest()


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


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


def get_formated_size(size):
    kb = 1024
    mb = kb*1024
    gb = mb*1024
    if size > gb:
        return f"{round(size/gb, 1)} GB"
    elif size > mb:
        return f"{round(size/mb, 1)} MB"
    elif size > kb:
        return f"{round(size/kb,1)} kB"
    else:
        return f"{size} bytes"


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


def calculate_backups():
    inits = return_init()
    if not inits:
        return None
    base_name, src_dir, backup_dir = inits

    sum_current = 0
    sum_all = 0
    for file_path in glob(pathname=f"*.blend[1-9]*", root_dir=backup_dir):
        p = Path(file_path)
        full_path = os.path.join(backup_dir, file_path)
        file_size = os.path.getsize(full_path)
        sum_all += file_size
        if base_name == p.with_suffix(".blend").name:
            sum_current += file_size
    return sum_current, sum_all


def clean_backup_folder(base_name: str, backup_dir: str) -> bool:
    prefs = prefs_object()
    files = glob(pathname=f"{base_name}[0-9]*", root_dir=backup_dir)
    for file in files:
        numerator = file[len(base_name):]
        if not f"{numerator}".isdigit():
            continue
        numerator = int(numerator)
        if numerator <= prefs.save_versions:
            continue
        src = os.path.join(backup_dir, f"{base_name}{numerator}")
        try:
            os.remove(src)
            print({'INFO'}, f'"{os.path.basename(src)}" successfully removed', {'FINISHED'})
        except:
            print({"ERROR"}, f'Can\'t remove "{os.path.basename(src)}"', {'CANCELLED'})
            return False
    return True


def get_all_save_versions(src_dir: str, backup_dir: str | None=None) -> set:
    get_files = lambda this_dir: (p.with_suffix(".blend").name for p in Path(this_dir).glob("[!.]*.blend[0-9]*"))
    output = set(get_files(src_dir))
    if backup_dir:
        output.union(set(get_files(backup_dir)))
    return output


def get_orphans(src_dir, backup_dir: str) -> dict:
    file_coll = dict()
    main_files = glob(pathname="[!.]*.blend", root_dir=src_dir)
    for file in iglob(pathname="[!.]*.blend[0-9]*", root_dir=backup_dir):
        p = Path(file)
        file_name = p.with_suffix(".blend").name
        if file_name in main_files:
            continue
        if file_name in file_coll:
            file_coll[file_name] += 1
        else:
            file_coll[file_name] = 1
    return file_coll


def get_numeric_version(pathname) -> int:
    p = Path(pathname)
    if p.name == p.with_suffix(".blend").name:
        return 0
    return int(p.name[len(p.with_suffix(".blend").name):])


def get_path_dir(inits: tuple) -> str:
    base_name, src_dir, backup_dir = inits
    path_dir = src_dir
    p = Path(base_name)
    if p.suffix == ".blend":
        path_dir = backup_dir
    return path_dir


def is_main_file(inits) -> bool:
    base_name, src_dir, backup_dir = inits
    p = Path(base_name)
    if p.suffix != ".blend":
        return False
    return True


def fix_backup_continuity(base_name: str, backup_dir: str) -> tuple[set[str], str, set[str]]:
    temp_files = []
    for file in iglob(f"{base_name}[0-9]*", root_dir=backup_dir):
        src = os.path.join(backup_dir, file)
        t = os.path.getmtime(src)
        temp = os.path.join(backup_dir, f"_TEMP_{file}")
        try:
            shutil.move(src, temp)
        except IOError:
            return {'ERROR'}, f"Error writing temporary files", {'CANCELLED'}
        except Exception:
            return {'ERROR'}, f"Can't rename a save file", {'CANCELLED'}
        temp_files.append((os.path.basename(temp), backup_dir, t))
    for i, record in enumerate(sorted(temp_files, key=lambda x: x[2], reverse=True)):
        file, saved_dir, _ = record
        src = os.path.join(saved_dir, file)
        dst = os.path.join(backup_dir, f"{base_name}{i + 1}")
        try:
            shutil.move(src, dst)
        except IOError:
            return {'ERROR'}, "Error renaming to a save version", {'CANCELLED'}
        except:
            return {'ERROR'}, "Can't rename to a save version", {'CANCELLED'}
    return {'INFO'}, "Fixing integrity successful", {'FINISHED'}


def rename_copies(new_base_name: str, old_base_name: str, backup_dir: str) -> tuple[set[str], str, set[str]]:
    p_new = Path(new_base_name)
    p_old = Path(old_base_name)
    path_name = "{}[0-9]*".format(p_old.with_suffix(".blend"))
    files = glob(pathname=path_name, root_dir=backup_dir)
    prefs = prefs_object()

    if not prefs.can_rename_overwrite:
        for file in files:
            p = Path(file)
            dst = Path(backup_dir, p.with_stem(p_new.stem))
            if dst.exists():
                return ({"ERROR"}, "Can't proceed if existing Save Versions get overwritten", {'CANCELLED'})

    for file in files:
        p = Path(file)
        src = Path(backup_dir, file)
        dst = Path(backup_dir, p.with_stem(p_new.stem))
        try:
            shutil.move(src, dst)
        except:
            return {"ERROR"}, f'Can\'t rename "{os.path.basename(src)}"', {'CANCELLED'}
    return {'INFO'}, "Successfully rename all Save Versions", {"FINISHED"}


def make_copies(base_name: str, src_dir: str, backup_dir: str) -> tuple[set[str], str, set[str]]:
    # Collect files for offsetting
    files = glob(pathname=f"{base_name}[0-9]*", root_dir=backup_dir)
    numerators = list(
        sorted(
            filter(
                None,
                (int(e[len(base_name):]) if (e[len(base_name):]).isdigit() else None for e in files)
            ),
            reverse=True
        )
    )
    # Offset existing Save Versions if any exists or skip
    if numerators:
        prefs = prefs_object()
        for suffix in numerators:
            if suffix >= prefs.save_versions:
                continue
            src = os.path.join(backup_dir, f"{base_name}{suffix}")
            dst = os.path.join(backup_dir, base_name + str(suffix + 1))
            try:
                shutil.copy2(src, dst)
            except FileExistsError:
                return {'ERROR'}, f"File \"{os.path.basename(dst)}\" exists at destination", {'CANCELLED'}
            except FileNotFoundError:
                return {'ERROR'}, f"Not such file as \"{os.path.basename(dst)}\"", {'CANCELLED'}

    # Copy the most current Save Version to a backup folder
    backup_name = f"{base_name}1"
    src = os.path.join(src_dir, backup_name)
    dst = os.path.join(backup_dir, backup_name)
    try:
        shutil.move(src, dst)
    except:
        return {'ERROR'}, f"Can't create Save Version \"{os.path.basename(dst)}\"", {'CANCELLED'}

    return {'INFO'}, f"Successfully backed up Save Versions", {'FINISHED'}


def move_copies(base_name: str, src_dir: str, backup_dir: str) -> typing.Tuple[set[str], str, set[str]]:
    files = []
    prefs = prefs_object()
    for file in iglob(f"{base_name}[0-9]*", root_dir=src_dir):
        src = os.path.join(src_dir, file)
        t = os.path.getmtime(src)
        files.append((file, src_dir, t))
    for file in iglob(f"{base_name}[0-9]*", root_dir=backup_dir):
        src = os.path.join(backup_dir, file)
        temp = os.path.join(backup_dir, f"_TEMP_{file}")
        t = os.path.getmtime(src)
        files.append((os.path.basename(temp), backup_dir, t))
        try:
            shutil.move(src, temp)
        except:
            return {'ERROR'}, f"Error moving temporary files", {'CANCELLED'}

    for i, element in enumerate(sorted(files, key=lambda x: x[2], reverse=True)):
        file, saved_dir, _ = element
        src = os.path.join(saved_dir, file)
        dst = os.path.join(backup_dir, f"{base_name}{i + 1}")
        try:
            shutil.move(src, dst)
        except:
            return {'ERROR'}, f"Error moving temporary files to \"{prefs.backup_folder_name}\"", {'CANCELLED'}

    return {'INFO'}, 'Moving files successful', {'FINISHED'}


class FileValidator:
    Methods = Enum("Methods", [("FILESIZE", 1), ("MD5", 2), ("SHA1", 3)])

    def __init__(self, pathname, method):
        self.method = method
        self.pathname = pathname
        self.number = -1
        self.text = ""
        self.__set(pathname)

    @staticmethod
    def __get_size(pathname):
        return os.path.getsize(pathname)

    def __get_hash(self, pathname):
        with open(pathname, "rb") as f_h:
            data = f_h.read()
        if self.method == self.Methods.MD5.name:
            return hashlib.md5(data).hexdigest()
        elif self.method == self.Methods.SHA1.name:
            return hashlib.sha1(data).hexdigest()
        else:
            raise ValueError("Unrecognised checksum method")

    def __set(self, pathname):
        if self.method == self.Methods.FILESIZE.name:
            self.number = self.__get_size(pathname)
        else:
            self.text = self.__get_hash(pathname)

    def __get(self):
        return self.number if self.method == self.Methods.FILESIZE.name else self.text

    def compare(self, pathname) -> bool:
        new_value = self.__get_size(pathname) if self.method == self.Methods.FILESIZE.name else self.__get_hash(
            pathname)
        return new_value == self.__get()


def update_on_pause(self, context):
    """This is a handler to update Blender System Settings when CBF change between
    states: on pause and active"""
    prefs = prefs_object()
    process_buildin_save_versions(not prefs.is_on_pause)


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


def vk_cbf_define_prev_next_popover(self, context):
    """Button in the header"""
    layout = self.layout
    layout.popover(
        panel="VK_PT_CBF_button_popover",  # should display the above Panel
        text="CBF",
        icon='DOCUMENTS'
    )


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


class VK_OT_CBF_RenameFiles(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Rename the project and corresponding Save Versions"""
    bl_idname = "vk_cbf.rename_files"
    bl_label = "Select File"
    bl_description = ("Select any Save Version from a sequence that represents the whole backup.\n"
                      "This will rename corresponding group of files to match the current main file.\n"
                      "Press Cancel to cancel the operation")

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
    bl_description = "Move Saved Versions to a backup folder. Affects only the current file." \
                     "\nIn case some Save Versions already exists in both folders, all files " \
                     "\nwill be merged and sorted by last modification date"

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
    bl_description = "Move all Saved Versions from a project folder to a custom folder." \
            "\nAll files will be merged and sorted in the reverse order by the last modification date"

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


class VK_OT_CBF_IssueReport(bpy.types.Operator):
    bl_idname = 'vk_cbf.report'
    bl_label = 'ReportStatus'

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
                     "\nCalculates and report the total size of all existing Save Versions." \
                     "\nThe report displays a sum of the current file and all existing project files."

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


class VK_OT_CBF_CleanUpOneFile(bpy.types.Operator):
    bl_idname = "vk_cbf.cleanup_one_file"
    bl_label = 'CleanUpBackupfolder'
    bl_description = "Clean up the backup folder"

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
    bl_description = "Clean up the backup folder"

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


class VK_EU_CBF_OpenCurrentFile(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "vk_cbf.open_browser_current"
    bl_label = "Brose Current"
    bl_description = "Browse backup folder for the current Save Version"

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


class VK_EU_CBF_OpenPreferences(bpy.types.Operator):
    bl_idname = "vk_cbf.open_addon_preferences"
    bl_label = "Open Addon Prefs"

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        bpy.context.preferences.active_section = 'ADDONS'
        bpy.context.window_manager.addon_search = bl_info.get("name")
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
        col.label(text="List of orphaned Save Versions not linked to any main file:")
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


class VK_PT_CBF_SaveChangesPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

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
        name="Auto Cleanup",
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
        row.prop(self, "can_rename_overwrite")
        row.prop(self, "is_on_pause")

