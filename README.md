# Introduction
This small tool provides a few improvements to manage Blender’s so-called **Saved Version** files.

By default, each time a project file is saved, Blender creates an additional **Saved Version**, which is essentially a copy of the current file saved under a similar name. These files have a distinct extension that ends with a number, which is incremented each time a new **Saved Version** is created.

Blender has a preference setting that controls a number of such files. This addon, however, provides its own preference, which is independent.

# The problem
One of the main issues is these files populate the main project folder. With only a single project file, this may not seem to be an issues and might look perfectly fine. However, as soon as artists create multiple backup copies of a project, the main folder will quickly become filled with a large number of files, which makes a bit  more difficult to navigate around the project folder.

This is where this add-on comes in. Its main functionality is to simply move these files to a separate folder and keep consecutive copies right there. Additionally, the add-on provides a few secondary tools to help maintain a backup folder. As en example, when the main project file is changed, Blender does not have any tool to keep integrity of back up files. This addon provides a function to rename all _orphan_ files to bind them back with the project files of a new name.

I find this addon useful and I hope it can offer the same QoL improvement to others.

# Installation
Simply drag and drop a ZIP archive into the Blender. This will automatically install and enable the addon.

# Usage
This is a simple tool that automatically moves Save Versions to a separate folder of your choice. It also provides several additional features for managing the folder containing your backup files.

## Access to the addon
The addon provides two panels:
- The main panel to the right activated with a key `N` and
- Supporting panel at the top of the 3D View window.

The main panel constains all functions provided by the addon, whereas the supporting panel provides buttons to open a backup folder as well as traverse through existing Save Versions.

## All functions
Access to the main functions is provided through the N-Panel (activated by pressing N). Simply press N and navigate to CBF.

Pleae be ware, all buttons are disabled until a project files is open because Save Versions are bound to a spedific project file.

Here is a list of all the available options and functions.

### Preferences
- `Open Preferences`

Navigates to the addon preference windows.

#### Addon Preferences
- `Save Versions`: Controls a number of backup files created by the Addon

**Please note**, the option _Save Version_ in the main Preferences in section `Save & Load` is required to be set to 1 for the addon to work. The addon manipulate this value when enabled/disabled/installed/uninstalled. **Please do not to change this value when Addon is active.**

- `Auto Clean`: Addon will automatically remove extensive **Save Versions** found in the backup folder on next save
- `Pause`: Simply temporary deactivates addons. **Importantly**, `Save Version` in the main Preferences in section `Save & Load` is temporarily restored. If this value was `0` when addon was installed, none Save Version file would be created.

### Traverse through existing backups
- `Previous` and `Next`
- _Search for Save Versions_ `Browse`

The first two buttons, `Previous` and `Next`, allow opening consecutive **Save Versions** from the backup folder, while the `Browse` button simply show a file browser in order to select a particular file to open.

### Moving existing backup files
- _Current project file_ `Move`
- _All project files_ `Move All`

By default, Blender creates **Save Versions** in the root project folder. The add-on may be installed when projects are already in progress. Additionally, if a project was already saved, new **Save Versions** would already exist.

The first button, `Move`, gathers all **Save Versions**, from both the project and backup folders, move files to the backup folder, and eventually sort the files by modification date in reverse order. As such, the most recent backup file will be named `<project file name>.blend1`. Only files related to the open project file are affected.

The other button `Move All` also moves **Save Versions**, but all files related to all project files are affected.

### Cleaning up the backup folder
- _Current project file_ `Clean`
- _All project files_ `Clean All`

In preferences, `Save Versions` (default 25) indicates how many **Save Verions** are kept in a backup folder. When this option is changed to a lower value, the addon will stop processing excessive backups, unless `Auto Clean` in Preferences is enabled. A user can also manually remove redundant files through `Clean` button.

While `Clean` only affects the current open file related **Save Versions**, `Clean All` will process all **Save Versions**.

### Renaming Save Versions
- _Select any Save Version_ `Rename`

When project file is renamed, **Blender** does not handle this situation automatically, so existing backup files need to be manually renamed.

To re-associate **Save Versions** with a new project file, press `Rename`. In the file browser, select any file that belongs to a group/sequence of **Save Versions** under the old name and press OK. Then add-on will rename the entire sequence, so that all files become associated with the project file.

If the renamed project file already created a new **Save Versions**, this option will also handle such situations meaning all files old and new will be renamed, and sorted according to their modification dates.

### Fix backup integrity
- _Press button to fix backups_ `Fix`

If we decide to delete some of the Save Versions, in the middle of the sequence, this button brings back the order.

### Reports
- _Report backup folder size_ `Report`
- _Show list of orphans_ `Show`

The first button reports two values: the total size of all **Save Versions** associated with the current project, and the total size of all **Save Versions**. This can be useful when working with multiple files with a large number of backups. Blender files can take even hundreds of megabytes each, so this function can be particularly useful for monitoring disk space. Please note that only Save Versions are counted.

If some backup files are not associated with any project file, `Show` will list those files. It will display only a single representation name. To see the entire sequence, simply navigate to the backup folder or use `Browse` button to open the folder (see above).