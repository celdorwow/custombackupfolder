import os
import shutil
from glob import glob, iglob
from pathlib import Path
from . ui_functions import prefs_object
from . utils_operators import return_init


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
