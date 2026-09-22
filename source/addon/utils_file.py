import os
import re
import shutil
import hashlib
import typing
from pathlib import Path
from enum import Enum
from glob import glob, iglob
from . ui_functions import prefs_object


def get_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f_h:
        data = f_h.read()
        return hashlib.md5(data).hexdigest()


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def get_numeric_version(pathname) -> int:
    p = Path(pathname)
    if p.name == p.with_suffix(".blend").name:
        return 0
    return int(p.name[len(p.with_suffix(".blend").name):])


def get_all_save_versions(src_dir: str, backup_dir: str | None=None) -> set:
    get_files = lambda this_dir: (p.with_suffix(".blend").name for p in Path(this_dir).glob("[!.]*.blend[0-9]*"))
    output = set(get_files(src_dir))
    if backup_dir:
        output.union(set(get_files(backup_dir)))
    return output


def sort_save_versions(save_versions: list) -> list:
    re_obj = re.compile(r"blend(\d+)$")
    if save_versions is None:
        raise ValueError("None of Save Version was found")
    return sorted(save_versions, key=lambda x: int(re_obj.search(x).group(1)))


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


def rename_copies(new_base_name: str, old_base_name: str, backup_dir: str) -> tuple[set[str], str, set[str]]:
    """This function process files when an existing main file was renamed, in order to bring integrity of
    all saved files"""
    prefs = prefs_object()

    # Gather file both current and old
    p_curr = Path(new_base_name)
    p_old = Path(old_base_name)
    path_name_old = "{}[0-9]*".format(p_old.with_suffix(".blend"))
    path_name_curr = "{}[0-9]*".format(p_curr.with_suffix(".blend"))
    existing_old = glob(pathname=path_name_old, root_dir=backup_dir)
    existing_curr = glob(pathname=path_name_curr, root_dir=backup_dir)
    all_files = set(existing_old).union(set(existing_curr))

    # Prepare files to sort and rename
    file_to_process = list()
    for file in all_files:
        src = os.path.join(backup_dir, file)
        temp = os.path.join(backup_dir, f"_TEMP_{file}")
        t = os.path.getmtime(src)
        file_to_process.append((os.path.basename(temp), t))
        try:
            shutil.move(src, temp)
        except:
            return {'ERROR'}, f"Error renaming a temporary file", {'CANCELLED'}
    file_to_process = sorted(file_to_process, key=lambda e: e[1], reverse=True)

    for i, e in enumerate(file_to_process):
        src = Path(backup_dir, e[0])
        dst = Path(backup_dir, p_curr.with_suffix(f".blend{i + 1}"))
        try:
            shutil.move(src, dst)
        except:
            return {"ERROR"}, f'Can\'t rename "{os.path.basename(src)}"', {'CANCELLED'}
    return {'INFO'}, "Successfully renamed all Save Versions", {"FINISHED"}


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


def is_main_file(inits) -> bool:
    base_name, src_dir, backup_dir = inits
    p = Path(base_name)
    if p.suffix != ".blend":
        return False
    return True


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
