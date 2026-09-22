# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# The main purpose of this piece of software is to improve management of
# Save Versions which Blender creates anytime a file is saved.
# Please note there is no WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    'name': 'Custom Backup Folder',
    'author': 'Celdor',
    'description': 'A backup tool with convenient tools',
    'blender': (4, 2, 0),
    'version': (0, 1, 2),
    'location': 'View3D',
    'category': '3D View'
}


ADDON_NAME = bl_info['name']
ADDON_VERSION = ".".join(map(str, bl_info['version']))

from . import addon


def register():
    addon.register()
    print("[INFO] {} v{} registered".format(ADDON_NAME, ADDON_VERSION))


def unregister():
    addon.unregister()
    print("[INFO] {} v{} unregistered".format(ADDON_NAME, ADDON_VERSION))
