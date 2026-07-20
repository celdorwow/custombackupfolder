# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# The main purpose and hope behind this small tool is that it will be useful,
# please note there is no WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    'name': 'CustomBackupFolder',
    'author': 'Celdor',
    'description': 'A backup tool with convenient tools',
    'blender': (4, 2, 0),
    'version': (0, 1, 0),
    'location': 'View3D',
    'wiki_url': 'www.github.com/cledorwow/cbf',
    'category': '3D View'
}


from . import addon


def register():
    addon.register()
    print("[INFO] Custom Backup Folder v{} registered".format(addon.main.cbf.version2str(bl_info["version"])))


def unregister():
    addon.unregister()
    print("[INFO] Custom Backup Folder v{} unregistered".format(addon.main.cbf.version2str(bl_info["version"])))
